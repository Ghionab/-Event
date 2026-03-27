$basePath = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'advanced - Copy')

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

    # Fix CSS caching issues by enforcing Tailwind utility classes directly on the logo variants
    # Also fix the logical display state because the gradient navbars don't have .bg-primary
    
    # We'll explicitly force the light logo to show and dark logo to hide in the navbars (which are always dark via gradients)
    $fixedDualLogo = @"
    <!-- Primary Logo for Light Contexts (Hidden in Dark Navbar) -->
    <img class="ea-logo hidden h-10 w-auto object-contain" src="{% static 'img/eventaxis-logo.png' %}" alt="EventAxis">
    <!-- Inverted Logo for Dark Contexts (Visible in Dark Navbar) -->
    <img class="ea-logo block h-10 w-auto object-contain" src="{% static 'img/eventaxis-logo-light.png' %}" alt="EventAxis">
"@

    $content = $content -replace '(?s)<!-- Primary Logo for Light Contexts -->\s*<img class="ea-logo ea-logo-dark-variant" src="{% static ''img/eventaxis-logo.png'' %}" alt="EventAxis">\s*<!-- Inverted Logo for Dark Contexts -->\s*<img class="ea-logo ea-logo-light-variant" src="{% static ''img/eventaxis-logo-light.png'' %}" alt="EventAxis">', $fixedDualLogo

    # Fix the standalone login logos to ensure they aren't massive either
    $content = $content -replace 'ea-logo ea-logo-dark-variant mx-auto mb-3', 'h-14 w-auto mx-auto mb-3 object-contain'
    $content = $content -replace 'ea-logo ea-logo-dark-variant mx-auto', 'h-14 w-auto mx-auto object-contain'
    $content = $content -replace 'ea-logo ea-logo-dark-variant', 'h-14 w-auto object-contain'

    if ($content -ne $original) {
        Set-Content $_.FullName -Value $content -NoNewline
        Write-Host "Forced Tailwind utility sizing on -> " $_.FullName
    }
}
