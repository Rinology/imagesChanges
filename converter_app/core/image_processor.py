import os
import threading
from io import BytesIO
from datetime import datetime
import send2trash
from PIL import Image
import shutil
import concurrent.futures
from converter_app.utils.naming_utils import get_pad_length

def _process_single_image(args):
    filepath, new_filepath, rot, method_val = args
    try:
        orig_size = os.path.getsize(filepath)
        
        with Image.open(filepath) as img:
            if rot != 0:
                img = img.rotate(rot, expand=True)
            if img.mode in ("RGBA", "LA", "P") or (img.mode == "RGB" and "transparency" in img.info):
                img = img.convert("RGBA")
                has_alpha = img.getchannel("A").getextrema()[0] < 255
            else:
                has_alpha = False
            
            if has_alpha:
                img.save(new_filepath, "webp", lossless=True, method=method_val)
            else:
                img.save(new_filepath, "webp", quality=80, method=method_val)
        
        new_size = os.path.getsize(new_filepath)
        size_diff = orig_size - new_size
        return (True, orig_size, new_size, size_diff, None)
    except Exception as e:
        return (False, 0, 0, 0, str(e))


class ImageProcessor:
    @staticmethod
    def _get_output_dir(file_dir: str, save_location: str, custom_path: str, subfolder_name: str, date_prefix: str, log: callable, run_time: datetime) -> str:
        """
        옵션에 따라 이미지가 저장될 최종 출력 디렉토리 경로를 생성하고 반환합니다.
        
        Args:
            file_dir (str): 원본 파일의 디렉토리 경로
            save_location (str): 'same'(현재 폴더), 'sub'(하위 폴더), 'custom'(새로운 경로)
            custom_path (str): 'custom' 선택 시 지정된 디렉토리 경로
            subfolder_name (str): 하위 폴더의 이름
            date_prefix (str): 'datetime', 'date', 'none' 중 하나로 접두어 설정
            log (callable): 로그 출력을 위한 콜백 함수
            run_time (datetime): 작업 시작 시간 (폴더명 일관성 유지)
            
        Returns:
            str: 생성된 출력 폴더의 절대 경로
        """
        if save_location == "custom" and custom_path:
            base_dir = custom_path
        else:
            base_dir = file_dir
            
        if save_location == "same":
            return base_dir
            
        # "sub" or "custom" with subfolder options
        prefix = ""
        if date_prefix == "datetime":
            prefix = run_time.strftime("%Y%m%d_%H%M%S") + "_"
        elif date_prefix == "date":
            prefix = run_time.strftime("%Y%m%d") + "_"
            
        folder_name = f"{prefix}{subfolder_name}" if subfolder_name else prefix.rstrip("_")
        
        if not folder_name and save_location == "custom":
            output_dir = base_dir
        else:
            if not folder_name:
                folder_name = "output"
            output_dir = os.path.join(base_dir, folder_name)
            
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                log(f"📂 폴더 생성됨: {output_dir}")
            except FileExistsError:
                pass
                
        return output_dir

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        바이트 단위의 파일 크기를 사람이 읽기 쉬운 문자열(KB, MB)로 변환합니다.
        
        Args:
            size_bytes (int): 바이트 단위 크기
            
        Returns:
            str: 포맷팅된 크기 문자열 (예: 1.5MB)
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.2f}MB"

    @staticmethod
    def calculate_expected_size_async(filepath, rotation, compression_method, callback_success, callback_error):
        """
        이미지 변환 시 예상되는 파일 크기를 비동기적으로 계산하여 콜백으로 전달합니다.
        
        Args:
            filepath (str): 대상 파일 경로
            rotation (int): 적용할 회전 각도
            compression_method (str|int): WebP 압축 옵션(method)
            callback_success (callable): 계산 성공 시 호출될 함수 (예상 크기 전달)
            callback_error (callable): 계산 실패 시 호출될 함수 (에러 메시지 전달)
        """
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
    def process_images_async(selected_files, raw_name, separator, save_location, subfolder_name, date_prefix, delete_orig, compression_method, rotations, callbacks, pad_mode="자동"):
        """
        선택된 여러 이미지 파일들을 비동기(멀티프로세싱)로 WebP 변환하고 저장합니다.
        
        Args:
            selected_files (list): 변환할 원본 파일의 절대 경로 리스트
            raw_name (str): 변경할 파일 이름의 베이스 텍스트
            separator (str): 파일 이름의 띄어쓰기를 대체할 연결 기호
            save_location (str): 저장 위치 옵션
            subfolder_name (str): 하위 폴더 사용 시 폴더 이름
            date_prefix (str): 접두어로 사용할 날짜 옵션
            delete_orig (bool): 변환 후 원본 파일 삭제 여부
            compression_method (str|int): WebP 압축 품질(method) 옵션
            rotations (dict): 각 파일별 적용할 회전 각도 딕셔너리
            callbacks (dict): 상태 업데이트를 위한 콜백 함수들 ('log', 'progress', 'done')
            pad_mode (str): 숫자 패딩 모드 (기본 "자동")
        """
        def process():
            log = callbacks.get('log', lambda m: None)
            progress_cb = callbacks.get('progress', lambda p, t: None)
            done_cb = callbacks.get('done', lambda s, e, b: None)
            
            log("🚀 변환 작업을 시작합니다... (멀티프로세싱 활성화됨)")
            total_files = len(selected_files)
            base_name = raw_name.replace(" ", separator)
            run_time = datetime.now()

            success_count = 0
            error_count = 0
            total_saved_bytes = 0
            last_output_dir = ""
            
            pad_length = get_pad_length(pad_mode, total_files)
            method_val = int(compression_method)
            
            tasks = []
            
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
            
            for i, filepath in enumerate(selected_files):
                idx = i + 1
                filename = os.path.basename(filepath)
                
                if not filepath.lower().endswith(valid_extensions):
                    log(f"⚠️ [{idx}/{total_files}] 사진 파일이 아니어서 건너뜁니다: {filename}")
                    progress_cb(idx, total_files)
                    continue
                    
                file_dir = os.path.dirname(filepath)
                output_dir = ImageProcessor._get_output_dir(
                    file_dir, save_location, callbacks.get('custom_path', ''),
                    subfolder_name, date_prefix, log, run_time
                )
                last_output_dir = output_dir
                
                if pad_length == 0:
                    new_filename = f"{base_name}.webp"
                else:
                    idx_str = str(idx).zfill(pad_length)
                    new_filename = f"{base_name}{separator}{idx_str}.webp"
                    
                new_filepath = os.path.join(output_dir, new_filename)
                
                # Check for duplicates if pad_length is 0 and there are multiple files
                if pad_length == 0 and total_files > 1 and i > 0:
                    new_filename = f"{base_name}({i}).webp"
                    new_filepath = os.path.join(output_dir, new_filename)
                
                rot = rotations.get(filepath, 0)
                
                tasks.append((filepath, new_filepath, rot, method_val, delete_orig, filename, idx, new_filename))

            completed = 0
            
            with concurrent.futures.ProcessPoolExecutor() as executor:
                future_to_task = {
                    executor.submit(_process_single_image, (t[0], t[1], t[2], t[3])): t for t in tasks
                }
                
                for future in concurrent.futures.as_completed(future_to_task):
                    t = future_to_task[future]
                    filepath, new_filepath, rot, method_val, delete_orig_flag, filename, idx, new_filename = t
                    try:
                        success, orig_size, new_size, size_diff, err = future.result()
                        if success:
                            if size_diff > 0:
                                total_saved_bytes += size_diff
                            
                            log_msg = f"✅ [{idx}/{total_files}] {filename} -> {new_filename} "
                            log_msg += f"(용량: {ImageProcessor.format_size(orig_size)} -> {ImageProcessor.format_size(new_size)})"
                            log(log_msg)
                            
                            if delete_orig_flag and filepath != new_filepath:
                                safe_filepath = os.path.normpath(os.path.abspath(filepath))
                                send2trash.send2trash(safe_filepath)
                                log(f"   🗑️ 원본이 휴지통으로 이동됨: {filename}")
                                
                            success_count += 1
                        else:
                            log(f"❌ [에러] {filename} 변환 실패: {err}")
                            error_count += 1
                    except Exception as e:
                        log(f"❌ [에러] {filename} 변환 실패 (크래시): {e}")
                        error_count += 1
                        
                    completed += 1
                    progress_cb(completed, total_files)
                    
            log(f"🎉 작업 완료! (성공: {success_count}, 에러: {error_count})")
            if total_saved_bytes > 0:
                log(f"💾 총 절감된 용량: {ImageProcessor.format_size(total_saved_bytes)}")
                
            done_cb(success_count, error_count, total_saved_bytes, last_output_dir)

        threading.Thread(target=process, daemon=True).start()

    @staticmethod
    def rename_images_async(selected_files, raw_name, separator, save_location, subfolder_name, date_prefix, delete_orig, callbacks, pad_mode="자동", target_ext="원본 유지"):
        """
        이미지 확장자 변경 없이 이름만 일괄 변경하거나 지정한 확장자로 단순 복사/이동합니다.
        
        Args:
            selected_files (list): 변경할 원본 파일의 절대 경로 리스트
            raw_name (str): 변경할 파일 이름의 베이스 텍스트
            separator (str): 파일 이름의 띄어쓰기를 대체할 연결 기호
            save_location (str): 저장 위치 옵션
            subfolder_name (str): 하위 폴더 사용 시 폴더 이름
            date_prefix (str): 접두어로 사용할 날짜 옵션
            delete_orig (bool): 복사 후 원본 파일 삭제(이동) 여부
            callbacks (dict): 상태 업데이트를 위한 콜백 함수들 ('log', 'progress', 'done')
            pad_mode (str): 숫자 패딩 모드 (기본 "자동")
            target_ext (str): 변경할 확장자 (기본 "원본 유지")
        """
        def process():
            log = callbacks.get('log', lambda m: None)
            progress_cb = callbacks.get('progress', lambda p, t: None)
            done_cb = callbacks.get('done', lambda s, e, b: None)
            
            log("🚀 이름 변경 작업을 시작합니다...")
            total_files = len(selected_files)
            base_name = raw_name.replace(" ", separator)
            run_time = datetime.now()

            success_count = 0
            error_count = 0
            last_output_dir = ""
            
            pad_length = get_pad_length(pad_mode, total_files)

            for i, filepath in enumerate(selected_files):
                idx = i + 1
                filename = os.path.basename(filepath)
                file_dir = os.path.dirname(filepath)
                
                output_dir = ImageProcessor._get_output_dir(
                    file_dir, save_location, callbacks.get('custom_path', ''),
                    subfolder_name, date_prefix, log, run_time
                )
                last_output_dir = output_dir
                
                if target_ext == "원본 유지":
                    ext = os.path.splitext(filename)[1]
                else:
                    ext = target_ext
                
                if pad_length == 0:
                    new_filename = f"{base_name}{ext}"
                else:
                    idx_str = str(idx).zfill(pad_length)
                    new_filename = f"{base_name}{separator}{idx_str}{ext}"
                    
                new_filepath = os.path.join(output_dir, new_filename)
                
                if pad_length == 0 and total_files > 1 and i > 0:
                    new_filename = f"{base_name}({i}){ext}"
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
            done_cb(success_count, error_count, 0, last_output_dir) # total_saved_bytes = 0

        threading.Thread(target=process, daemon=True).start()

    @staticmethod
    def create_thumbnail(filepath, rotation, max_size=(550, 550)):
        """
        UI 미리보기를 위해 이미지의 썸네일을 생성하고 Base64 문자열로 반환합니다.
        
        Args:
            filepath (str): 원본 파일 경로
            rotation (int): 적용할 회전 각도
            max_size (tuple): 썸네일 최대 너비/높이
            
        Returns:
            str: Base64로 인코딩된 PNG 이미지 데이터
        """
        import base64
        with Image.open(filepath) as img:
            if rotation != 0:
                img = img.rotate(rotation, expand=True)
            img.thumbnail(max_size)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
