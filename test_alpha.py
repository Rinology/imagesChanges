from PIL import Image

def analyze_alpha(img_path):
    with Image.open(img_path) as img:
        print(f"{img_path}: mode={img.mode}")
        if img.mode in ("RGBA", "LA"):
            alpha = img.getchannel("A")
            extrema = alpha.getextrema()
            print(f"Alpha extrema: {extrema}")
            # If extrema is (255, 255), it's fully opaque.
            return extrema[0] < 255
    return False

# Analyze original
print("Original X_Logo_Black.png has transparency:", analyze_alpha("X_Logo_Black.png"))

# Create conversions
with Image.open("X_Logo_Black.png") as img:
    # 1. Direct save
    img.save("test1.webp", "webp", quality=80)
    # 2. RGB
    img.convert("RGB").save("test2.webp", "webp", quality=80)

print("test1.webp has transparency:", analyze_alpha("test1.webp"))
print("test2.webp has transparency:", analyze_alpha("test2.webp"))
