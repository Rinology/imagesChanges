import os

def get_pad_length(pad_mode: str, total_files: int) -> int:
    if pad_mode == "지정안함":
        return 1
    elif pad_mode == "자동":
        return len(str(total_files)) if total_files > 0 else 1
    elif pad_mode == "2자리":
        return 2
    elif pad_mode == "3자리":
        return 3
    elif pad_mode == "4자리":
        return 4
    elif pad_mode == "5자리":
        return 5
    elif pad_mode == "6자리":
        return 6
    return 1

def generate_new_filename(original_filename: str, idx: int, settings: dict, total_files: int) -> str:
    """
    Generates a new filename based on settings.
    """
    mode = settings.get('mode', 'compress')
    raw_name = settings.get('raw_name', '').strip()
    separator = settings.get('separator', '_')
    pad_mode = settings.get('pad_mode', '자동')
    
    base_name = raw_name.replace(" ", separator) if raw_name else "이름없음"
    pad_length = get_pad_length(pad_mode, total_files)
    idx_str = str(idx).zfill(pad_length)
    
    if mode == 'compress':
        return f"{base_name}{separator}{idx_str}.webp"
    else:
        target_ext = settings.get('target_ext', '원본 유지')
        if target_ext == "원본 유지":
            ext = os.path.splitext(original_filename)[1]
        else:
            ext = target_ext
        return f"{base_name}{separator}{idx_str}{ext}"
