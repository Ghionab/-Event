import sys
import subprocess

# Ensure Pillow is installed
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image

def trim_transparent_edges(image_path):
    try:
        # Open image
        img = Image.open(image_path).convert("RGBA")
        
        # Get the bounding box of non-zero alpha (non-transparent pixels)
        # getbbox() works on the truth value of pixels. For RGBA, full transparent is (0,0,0,0)
        # However, to be highly precise, we map it:
        bbox = img.split()[-1].getbbox()
        
        if bbox:
            print(f"Original size: {img.size}, Bounding box: {bbox}")
            # Crop to the bounding box
            cropped_img = img.crop(bbox)
            print(f"New size: {cropped_img.size}")
            
            # Note: We keep a tiny 1% padding just for aesthetic breathing room, or zero padding
            # Let's do absolute zero padding to fit the SaaS geometric standards.
            
            cropped_img.save(image_path, format="PNG")
            print(f"✅ Successfully trimmed: {image_path}\n")
        else:
            print(f"Image might be totally transparent or empty: {image_path}\n")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}\n")

if __name__ == "__main__":
    assets = [
        r"c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\static\img\eventaxis-logo.png",
        r"c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\static\img\eventaxis-logo-light.png"
    ]
    
    for asset in assets:
        print(f"Processing: {asset}")
        trim_transparent_edges(asset)
