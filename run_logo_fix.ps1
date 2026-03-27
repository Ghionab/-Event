$basePath = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'advanced - Copy')

# 1. First, fix the 404 broken 'eventaxis-logo-dark.png' across login screens
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

    # Fix bogus dark logo name -> real primary logo (eventaxis-logo.png)
    $content = $content -replace 'eventaxis-logo-dark.png', 'eventaxis-logo.png'
    
    # Inject the actual ea-logo-dark-variant structure for login files
    $content = $content -replace "class=`"h-14 w-auto mx-auto mb-3`"", "class=`"ea-logo ea-logo-dark-variant mx-auto mb-3`""
    $content = $content -replace "class=`"h-14 w-auto mx-auto`"", "class=`"ea-logo ea-logo-dark-variant mx-auto`""
    $content = $content -replace "class=`"h-14 w-auto`"", "class=`"ea-logo ea-logo-dark-variant`""

    # Navbar explicit images (e.g. organizer/events/coordinator base.html)
    $dualLogo = @"
    <!-- Primary Logo for Light Contexts -->
    <img class="ea-logo ea-logo-dark-variant" src="{% static 'img/eventaxis-logo.png' %}" alt="EventAxis">
    <!-- Inverted Logo for Dark Contexts -->
    <img class="ea-logo ea-logo-light-variant" src="{% static 'img/eventaxis-logo-light.png' %}" alt="EventAxis">
"@

    # Replace legacy single image in navbars using eventaxis-logo-light.png
    # Specifically targeting the <img ... >
    $content = $content -replace '(?s)<img\s+src="{% static ''img/eventaxis-logo-light.png'' %}"\s+alt="EventAxis"\s+class="h-10 w-auto">', $dualLogo
    $content = $content -replace '(?s)<img\s+src="{% static ''img/eventaxis-logo-light.png'' %}"\s+alt="EventAxis"\s+class="h-12 w-auto">', $dualLogo

    if ($content -ne $original) {
        Set-Content $_.FullName -Value $content -NoNewline
        Write-Host "Replaced Logo Patterns In -> " $_.FullName
    }
}
