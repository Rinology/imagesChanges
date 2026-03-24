import os
import re

def translate_korean_filenames(target_folder):
    # 1. 영문 번역 사전 (형이 긴 단어부터 먼저 처리되도록 순서를 꼼꼼하게 배치했어!)
    korean_to_eng = {
        "프로미니-맥스": "prominimax",
        "프로-맥스": "promax",
        "시티-맥스": "citymax",
        "투어-맥스": "tourmax",
        "상세페이지": "detail",
        "GT미니": "gtmini",
        "프로미니": "promini",
        "엑스트론": "xtron",
        "시티": "city",
        "미니": "mini",
        "프로S": "pros",
        "프로": "pro",
        "슬림": "slim",
        "투어": "tour"
    }

    for root, dirs, files in os.walk(target_folder):
        for filename in files:
            new_filename = filename

            # 2. 마법의 정규식: '01' 뒤에 붙은 잡다한 글자 삭제하고 '.확장자' 만 남기기
            # (설명: '01'부터 점(.)이 나오기 전까지의 모든 문자를 찾아 '01.'으로 덮어씀)
            new_filename = re.sub(r'(\d+)[가-힣]+\.', r'\1.', new_filename)

            # 3. 한글 ➔ 영문 치환 로직
            for kr, eng in korean_to_eng.items():
                if kr in new_filename:
                    new_filename = new_filename.replace(kr, eng)

            # 4. SEO를 위한 최종 마무리: 혹시 모를 대문자를 전부 소문자로 통일!
            new_filename = new_filename.lower()

            # 이름이 변경되었다면 덮어쓰기
            if new_filename != filename:
                old_filepath = os.path.join(root, filename)
                new_filepath = os.path.join(root, new_filename)
                
                try:
                    os.rename(old_filepath, new_filepath)
                    print(f"✅ 변환 완료: {filename} ➔ {new_filename}")
                except Exception as e:
                    print(f"❌ 변환 실패 ({filename}): {e}")

if __name__ == "__main__":
    TARGET_DIR = "./images"  # 타겟 폴더 경로
    
    print("🚀 한글 파일명 영문 번환 및 01 정리 스크립트를 시작합니다...")
    translate_korean_filenames(TARGET_DIR)
    print("🎉 모든 변환이 완료되었습니다! 이제 이름이 완벽해졌습니다!")