import os

def replace_underscore_with_hyphen(target_folder):
    # os.walk를 쓰면 최상위 폴더뿐만 아니라 하위 폴더(detail 등)까지 싹 다 뒤져줌!
    for root, dirs, files in os.walk(target_folder):
        for filename in files:
            # 파일 이름에 언더바(_)가 들어있는 파일만 타겟으로 삼음 (파이썬 코드나 숨김 파일 등은 안전을 위해 제외)
            if "_" in filename and not filename.endswith('.py') and not filename.startswith('.'):
                # _ 를 - 로 바꾼 새 파일 이름 만들기
                new_filename = filename.replace("_", "-")
                
                # 파일의 원래 전체 경로와 새 전체 경로 만들기
                old_filepath = os.path.join(root, filename)
                new_filepath = os.path.join(root, new_filename)
                
                try:
                    # 파일 이름 강제 개명!
                    os.rename(old_filepath, new_filepath)
                    print(f"✅ 변환 완료: {filename} ➔ {new_filename}")
                except Exception as e:
                    print(f"❌ 변환 실패 ({filename}): {e}")

if __name__ == "__main__":
    # 🎯 타겟 폴더 설정 (현재 폴더('.')를 지정하여 모든 하위 폴더를 탐색)
    TARGET_DIR = "." 
    
    print("🚀 구글 SEO 1등을 위한 파일명 하이픈(-) 변환을 시작합니다...")
    
    if os.path.exists(TARGET_DIR):
        replace_underscore_with_hyphen(TARGET_DIR)
        print("🎉 모든 변환이 완료되었습니다! 이제 Cloudinary에 다시 올릴 준비 끝!")
    else:
        print(f"⚠️ 에러: '{TARGET_DIR}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")