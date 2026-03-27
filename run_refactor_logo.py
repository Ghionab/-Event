import os
import re

base_path = r"c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"
exclude_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'advanced - Copy'}

# The new unified 36px standard logo inverted to white
single_logo_html = '''<!-- Single-Source Logo System (eventaxis-logo.png) -->
<img class="ea-logo" src="{% static 'img/eventaxis-logo.png' %}" alt="EventAxis" style="height: 36px; width: auto; object-fit: contain; filter: brightness(0) invert(1);">'''

regex_pattern = re.compile(
    r'<!-- Primary Logo for Light Contexts.*?<img class="ea-logo block dark:hidden".*?>',
    re.DOTALL
)

for root, dirs, files in os.walk(base_path):
    # Prune excluded dirs
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if '<!-- Primary Logo for Light Contexts' in content:
                new_content = regex_pattern.sub(single_logo_html, content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Refactored: {file_path}")

# Delete the light logo
light_logo = os.path.join(base_path, 'static', 'img', 'eventaxis-logo-light.png')
if os.path.exists(light_logo):
    os.remove(light_logo)
    print(f"\nDELETED REDUNDANT ASSET: {light_logo}")
