import os
import shutil
import zipfile
import re

def main():
    print("Starting deployment build for cPanel...")
    
    # 1. Define paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    build_dir = os.path.join(base_dir, 'cpanel_build')
    zip_path = os.path.join(base_dir, 'eventaxis_deploy.zip')
    
    # Clean previous build
    if os.path.exists(build_dir):
        print("Cleaning old build folder...")
        shutil.rmtree(build_dir)
        
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Creating build folder at: {build_dir}")
    os.makedirs(build_dir)
    
    # Directories/Files to ignore when copying
    ignore_patterns = shutil.ignore_patterns(
        '.git', 
        'venv', 
        'env', 
        '__pycache__', 
        '.vscode',
        'cpanel_build',
        'eventaxis_deploy.zip',
        'db.sqlite3',      # Optional: exclude DB so fresh start on server
        '.claude',
        '.claude - Copy',
        '*.bat',
        '*.ps1',
        '*.cmd'
    )
    
    # 2. Copy files to build directory
    print("Copying files to build directory... (This may take a minute)")
    for item in os.listdir(base_dir):
        s = os.path.join(base_dir, item)
        d = os.path.join(build_dir, item)
        # Skip ignored paths
        if any(ignored in item for ignored in ['.git', 'venv', 'env', '__pycache__', 'cpanel_build', 'eventaxis_deploy.zip']):
            continue
            
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=ignore_patterns, dirs_exist_ok=True)
        else:
            # Manually check ignore list for top-level files
            if not any(item.endswith(ext) for ext in ['.bat', '.ps1', '.cmd']) and item not in ['db.sqlite3']:
                shutil.copy2(s, d)
                
    # 3. Modify settings.py for production
    print("Modifying settings.py for production environment...")
    settings_path = os.path.join(build_dir, 'event_project', 'settings.py')
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_content = f.read()
        
    # Replace DEBUG = True with False
    settings_content = re.sub(r'DEBUG\s*=\s*True', 'DEBUG = False', settings_content)
    
    # Replace ALLOWED_HOSTS (handling current `['*']`)
    settings_content = re.sub(
        r"ALLOWED_HOSTS\s*=\s*\[.*\]", 
        "ALLOWED_HOSTS = ['yegar.com', 'www.yegar.com', '*']", 
        settings_content
    )
    
    # Add STATIC_ROOT if it doesn't exist
    if 'STATIC_ROOT' not in settings_content:
        # Find STATIC_URL to place it nearby
        settings_content = settings_content.replace(
            "STATIC_URL = 'static/'",
            "STATIC_URL = 'static/'\nSTATIC_ROOT = BASE_DIR / 'staticfiles'"
        )
        # Fallback if the replacement didn't work exactly
        if 'STATIC_ROOT' not in settings_content:
            settings_content += "\n\n# Added for cPanel deployment\nSTATIC_ROOT = BASE_DIR / 'staticfiles'\n"
            
    # Modify CORS to add yegar.com domains
    settings_content = settings_content.replace(
        'CORS_ALLOWED_ORIGINS = [',
        'CORS_ALLOWED_ORIGINS = [\n    "https://yegar.com",\n    "https://www.yegar.com",'
    )

    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_content)
        
    # 4. Create the deployment Zip file
    print("Zipping the build folder...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate relative path to store in zip correctly
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
                
    # 5. Cleanup
    print("Cleaning up temporary build files...")
    shutil.rmtree(build_dir)
    
    print("\n✅ Build Successful!")
    print(f"Your deployment file is ready at: {zip_path}")
    print("You can upload this zip file directly to your cPanel File Manager!")

if __name__ == "__main__":
    main()
