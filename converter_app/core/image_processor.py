import os
import threading
from io import BytesIO
from datetime import datetime
import send2trash
from PIL import Image
import shutil

class ImageProcessor:
    @staticmethod
    def _get_output_dir(folder_path: str, save_location: str, subfolder_name: str, date_prefix: str, log: callable) -> str:
        output_dir = folder_path
        if save_location == "sub":
            now = datetime.now()
            prefix = ""
            if date_prefix == "datetime":
                prefix = now.strftime("%Y%m%d_%H%M%S") + "_"
            elif date_prefix == "date":
                prefix = now.strftime("%Y%m%d") + "_"
                
            folder_name = f"{prefix}{subfolder_name}" if subfolder_name else prefix.rstrip("_")
            if not folder_name:
                folder_name = "output"
                
            output_dir = os.path.join(folder_path, folder_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                log(f"📂 폴더 생성됨: {output_dir}")
        return output_dir

    @staticmethod
    def format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.2f}MB"

    @staticmethod
    def calculate_expected_size_async(filepath, rotation, compression_method, callback_success, callback_error):
        def calc():
            try:
                method_val = int(compression_method)
                with Image.open(filepath) as img:
                    if rotation != 0:
                        img = img.rotate(rotation, expand=True)
                    if img.mode in ("RGBA", "LA", "P") or (img.mode == "RGB" and "transparency" in img.info):
                        img = img.convert("RGBA")
                        has_alpha = img.getchannel("A").getextrema()[0] < 255
                    else:
                        has_alpha = False
                    
                    buffer = BytesIO()
                    if has_alpha:
                        img.save(buffer, format="webp", lossless=True, method=method_val)
                    else:
                        img.save(buffer, format="webp", quality=80, method=method_val)
                    expected = len(buffer.getvalue())
                
                callback_success(expected)
            except Exception as e:
                callback_error(str(e))
        
        threading.Thread(target=calc, daemon=True).start()

    @staticmethod
    def process_images_async(selected_files, folder_path, raw_name, separator, save_location, subfolder_name, date_prefix, delete_orig, compression_method, rotations, callbacks):
        """
        callbacks: dict with keys 'log', 'progress', 'done'
        selected_files: list of filenames to process
        rotations: dict of filepath to rotation degrees
        """
        def process():
            log = callbacks.get('log', lambda m: None)
            progress_cb = callbacks.get('progress', lambda p, t: None)
            done_cb = callbacks.get('done', lambda s, e, b: None)
            
            log("🚀 변환 작업을 시작합니다...")
            total_files = len(selected_files)
            base_name = raw_name.replace(" ", separator)
            
            output_dir = ImageProcessor._get_output_dir(folder_path, save_location, subfolder_name, date_prefix, log)

            success_count = 0
            error_count = 0
            total_saved_bytes = 0
            
            for i, filename in enumerate(selected_files):
                idx = i + 1
                filepath = os.path.join(folder_path, filename)
                new_filename = f"{base_name}{separator}{idx}.webp"
                new_filepath = os.path.join(output_dir, new_filename)
                
                try:
                    orig_size = os.path.getsize(filepath)
                    
                    with Image.open(filepath) as img:
                        rot = rotations.get(filepath, 0)
                        if rot != 0:
                            img = img.rotate(rot, expand=True)
                        if img.mode in ("RGBA", "LA", "P") or (img.mode == "RGB" and "transparency" in img.info):
                            img = img.convert("RGBA")
                            has_alpha = img.getchannel("A").getextrema()[0] < 255
                        else:
                            has_alpha = False
                        
                        method_val = int(compression_method)
                        if has_alpha:
                            img.save(new_filepath, "webp", lossless=True, method=method_val)
                        else:
                            img.save(new_filepath, "webp", quality=80, method=method_val)
                    
                    new_size = os.path.getsize(new_filepath)
                    size_diff = orig_size - new_size
                    if size_diff > 0:
                        total_saved_bytes += size_diff
                    
                    log_msg = f"✅ [{idx}/{total_files}] {filename} -> {new_filename} "
                    log_msg += f"(용량: {ImageProcessor.format_size(orig_size)} -> {ImageProcessor.format_size(new_size)})"
                    log(log_msg)
                    
                    if delete_orig and filepath != new_filepath:
                        send2trash.send2trash(filepath)
                        log(f"   🗑️ 원본이 휴지통으로 이동됨: {filename}")
                        
                    success_count += 1
                except Exception as e:
                    log(f"❌ [에러] {filename} 변환 실패: {e}")
                    error_count += 1
                    
                progress_cb(idx, total_files)
                    
            log(f"🎉 작업 완료! (성공: {success_count}, 에러: {error_count})")
            if total_saved_bytes > 0:
                log(f"💾 총 절감된 용량: {ImageProcessor.format_size(total_saved_bytes)}")
                
            done_cb(success_count, error_count, total_saved_bytes)

        threading.Thread(target=process, daemon=True).start()

    @staticmethod
    def rename_images_async(selected_files, folder_path, raw_name, separator, save_location, subfolder_name, date_prefix, delete_orig, callbacks, pad_mode="자동", target_ext="원본 유지"):
        """
        callbacks: dict with keys 'log', 'progress', 'done'
        selected_files: list of filenames to process in order
        pad_mode: string, "자동", "지정안함", "2자리" 등
        target_ext: string, "원본 유지" 또는 ".png" 등
        """
        def process():
            log = callbacks.get('log', lambda m: None)
            progress_cb = callbacks.get('progress', lambda p, t: None)
            done_cb = callbacks.get('done', lambda s, e, b: None)
            
            log("🚀 이름 변경 작업을 시작합니다...")
            total_files = len(selected_files)
            base_name = raw_name.replace(" ", separator)
            
            output_dir = ImageProcessor._get_output_dir(folder_path, save_location, subfolder_name, date_prefix, log)

            success_count = 0
            error_count = 0
            
            if pad_mode == "지정안함": pad_length = 1
            elif pad_mode == "자동": pad_length = len(str(total_files))
            elif pad_mode == "2자리": pad_length = 2
            elif pad_mode == "3자리": pad_length = 3
            elif pad_mode == "4자리": pad_length = 4
            elif pad_mode == "5자리": pad_length = 5
            elif pad_mode == "6자리": pad_length = 6
            else: pad_length = 1

            for i, filename in enumerate(selected_files):
                idx = i + 1
                filepath = os.path.join(folder_path, filename)
                if target_ext == "원본 유지":
                    ext = os.path.splitext(filename)[1]
                else:
                    ext = target_ext
                idx_str = str(idx).zfill(pad_length)
                
                new_filename = f"{base_name}{separator}{idx_str}{ext}"
                new_filepath = os.path.join(output_dir, new_filename)
                
                try:
                    if os.path.abspath(filepath) == os.path.abspath(new_filepath):
                        log(f"⚠️ [{idx}/{total_files}] 변경할 이름이 기존과 동일하여 건너뜁니다: {filename}")
                        success_count += 1
                        progress_cb(idx, total_files)
                        continue

                    if delete_orig:
                        # 원본 삭제(이동)
                        shutil.move(filepath, new_filepath)
                        log(f"✅ [{idx}/{total_files}] (이동) {filename} -> {new_filename}")
                    else:
                        # 원본 유지(복사)
                        shutil.copy2(filepath, new_filepath)
                        log(f"✅ [{idx}/{total_files}] (복사) {filename} -> {new_filename}")
                        
                    success_count += 1
                except Exception as e:
                    log(f"❌ [에러] {filename} 처리 실패: {e}")
                    error_count += 1
                    
                progress_cb(idx, total_files)
                    
            log(f"🎉 이름 변경 완료! (성공: {success_count}, 에러: {error_count})")
            done_cb(success_count, error_count, 0) # total_saved_bytes = 0

        threading.Thread(target=process, daemon=True).start()

    @staticmethod
    def create_thumbnail(filepath, rotation, max_size=(550, 550)):
        import base64
        with Image.open(filepath) as img:
            if rotation != 0:
                img = img.rotate(rotation, expand=True)
            img.thumbnail(max_size)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
