$basePath = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'advanced - Copy')

# The robust, unbreakable dual-logo template (with explicit inline styles protecting against CSS compilation failure)
$robustDualLogo = @"
    <!-- Primary Logo for Light Contexts (Hidden in Dark Navbar) -->
    <img class="ea-logo hidden dark:block" src="{% static 'img/eventaxis-logo.png' %}" alt="EventAxis" style="height: 36px; width: auto; object-fit: contain; display: var(--ea-logo-display-light, none);">
    <!-- Inverted Logo for Dark Contexts (Visible in Dark Navbar) -->
    <img class="ea-logo block dark:hidden" src="{% static 'img/eventaxis-logo-light.png' %}" alt="EventAxis" style="height: 36px; width: auto; object-fit: contain; display: var(--ea-logo-display-dark, block);">
"@

Get-ChildItem -Path $basePath -Recurse -Filter *.html | Where-Object {
    $path = $_.FullName
    $skip = $false
    foreach ($dir in $excludeDirs) {
        if ($path -match "\\$dir\\") { $skip = $true; break }
    }
    -not $skip
} | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $original = $content

    # Target the fragile logo block and string-replace it with the robust one 
    $content = $content -replace '(?s)<!-- Primary Logo for Light Contexts \(Hidden in Dark Navbar\) -->\s*<img class="ea-logo hidden h-10 w-auto object-contain" src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis">\s*<!-- Inverted Logo for Dark Contexts \(Visible in Dark Navbar\) -->\s*<img class="ea-logo block h-10 w-auto object-contain" src="{% static ''img/eventaxis-logo-light.png'' %}" alt="EventAxis">', $robustDualLogo
    
    # Also fix the login logos to have robust inline styles
    $content = $content -replace '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="h-14 w-auto mx-auto mb-3 object-contain">', '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="ea-logo mx-auto mb-3" style="height: 48px; width: auto; object-fit: contain;">'
    $content = $content -replace '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="h-14 w-auto mx-auto object-contain">', '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="ea-logo mx-auto" style="height: 48px; width: auto; object-fit: contain;">'
    $content = $content -replace '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="h-14 w-auto object-contain">', '<img src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis" class="ea-logo" style="height: 48px; width: auto; object-fit: contain;">'

    if ($content -ne $original) {
        Set-Content $_.FullName -Value $content -NoNewline
        Write-Host "Robust architectural constraints enforced on -> " $_.FullName
    }
}
