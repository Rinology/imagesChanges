import os

from PIL import Image



def convert_to_webp(source_folder, output_folder, quality=80):

    # 결과물을 저장할 폴더가 없으면 새로 만든다

    if not os.path.exists(output_folder):

        os.makedirs(output_folder)



    # 폴더 안의 모든 하위 폴더와 파일을 재귀적으로 확인
    for root, dirs, files in os.walk(source_folder):
        # 최적화 결과물을 저장할 폴더는 변환 대상에서 제외 (무한루프 방지)
        if os.path.abspath(root) == os.path.abspath(output_folder):
            continue

        for filename in files:
            # 확장자가 png, jpg, jpeg인 것만 골라냄 (대소문자 무시)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(root, filename)
                
                try:
                    # 이미지 열기
                    img = Image.open(filepath)
                    
                    # 파일 이름만 빼오기
                    file_name_without_ext = os.path.splitext(filename)[0]
                    
                    # 원래 폴더의 하위 구조를 유지하면서 저장할 경로 생성
                    rel_dir = os.path.relpath(root, source_folder)
                    target_dir = os.path.join(output_folder, rel_dir)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)

                    # 저장할 경로와 이름 설정 (.webp로)
                    new_filepath = os.path.join(target_dir, f"{file_name_without_ext}.webp")
                    
                    # WebP 포맷으로 저장
                    img.save(new_filepath, 'webp', quality=quality)
                    
                    # 출력시 상대 경로로 띄워주기
                    rel_path = os.path.relpath(filepath, source_folder)
                    print(f"✅ 변환 성공: {rel_path} -> {os.path.join(rel_dir, file_name_without_ext)}.webp")
                    
                except Exception as e:
                    print(f"❌ 변환 실패 ({filepath}): {e}")



# 실행 부분 (source_folder에 네 원본 이미지 폴더 이름을 넣어)

if __name__ == "__main__":

    SOURCE_DIR = "."       

    OUTPUT_DIR = "./optimized_webp"

    

    print("🚀 이미지 최적화를 시작합니다...")

    convert_to_webp(SOURCE_DIR, OUTPUT_DIR)

    print("🎉 모든 변환이 완료되었습니다! Vercel 요금이 굳었습니다.")