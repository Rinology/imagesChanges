from PIL import Image

def test_convert(filepath):
    print(f"\n--- Testing {filepath} ---")
    with Image.open(filepath) as img:
        print(f"Original mode: {img.mode}")
        print(f"Original info: {img.info}")
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode in ("L", "LA", "P"): # Check if we need any other conversions
            pass
        
        # Test saving as webp without explicit conversion
        img.save(filepath + "_test.webp", "webp", quality=80)

test_convert("X_Logo_Black.png")
test_convert("X_Logo_Wihte.png")
