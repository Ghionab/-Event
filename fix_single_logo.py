import sys
import subprocess

try:
    from PIL import Image
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "numpy"])
    from PIL import Image
    import numpy as np

def fix_logo(image_path):
    print(f"Processing {image_path}...")
    try:
        img = Image.open(image_path).convert("RGBA")
        data = np.array(img)
        
        # Identify near-white pixels (background)
        r, g, b, a = data.T
        white_areas = (r > 245) & (g > 245) & (b > 245)
        
        # set alpha to 0 for these pixels
        data[..., 3][white_areas.T] = 0
        
        transparent_img = Image.fromarray(data)
        
        # Calculate bounding box of non-transparent elements
        bbox = transparent_img.getbbox()
        if bbox:
            print(f"Original bbox string: {bbox}")
            # Add a microscopic 2px padding for anti-aliasing safety
            pad = 2
            safe_bbox = (
                max(0, bbox[0] - pad),
                max(0, bbox[1] - pad),
                min(transparent_img.width, bbox[2] + pad),
                min(transparent_img.height, bbox[3] + pad)
            )
            
            cropped = transparent_img.crop(safe_bbox)
            cropped.save(image_path, format="PNG")
            print(f"SUCCESS: Removed white background and cropped perfectly to: {cropped.size} (from {img.size})")
        else:
            print("WARNING: Image is completely transparent.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    logo_path = r"c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\static\img\eventaxis-logo.png"
    fix_logo(logo_path)
