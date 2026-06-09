import os
import threading
from io import BytesIO
from datetime import datetime
import send2trash
from PIL import Image, ImageTk

class ImageProcessor:
    @staticmethod
    def format_size(size_bytes):
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
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    buffer = BytesIO()
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
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        method_val = int(compression_method)
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
    def create_thumbnail(filepath, rotation, max_size=(550, 550)):
        img = Image.open(filepath)
        if rotation != 0:
            img = img.rotate(rotation, expand=True)
        img.thumbnail(max_size)
        return ImageTk.PhotoImage(img)
