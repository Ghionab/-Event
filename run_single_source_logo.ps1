$basePath = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'advanced - Copy')

# 1. Delete the redundant asset
$lightLogoPath = Join-Path $basePath "static\img\eventaxis-logo-light.png"
if (Test-Path $lightLogoPath) {
    Remove-Item -Path $lightLogoPath -Force
    Write-Host "DELETED REDUNDANT LOGO: $lightLogoPath"
}

# 2. The new robust SINGLE-SOURCE logo template for dark navbars
# We apply brightness(0) invert(1) to perfectly turn the dark blue/gold PNG into a pure white vector-style logo
$singleLogoNavbar = @"
    <!-- Single-Source Logo System (Asset: eventaxis-logo.png) (Filter applied for dark navbars) -->
    <img class="ea-logo" src="{% static 'img/eventaxis-logo.png' %}" alt="EventAxis" style="height: 36px; width: auto; object-fit: contain; max-height: 100%; filter: brightness(0) invert(1);">
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

    # Target the fragile/robust dual-logo blocks from previous iterations
    # Match the entire block from <!-- Primary Logo to display: var(--ea-logo-display-dark, block);">
    
    $regexDualBlock = '(?s)<!-- Primary Logo for Light Contexts.*?display: var\(--ea-logo-display-dark, block\);">\s*(?:</a>|)'
    
    # We carefully replace the entire chunk with the single logo inside the anchor
    # But wait, our previous regex didn't include </a>. Let's just match the two exact img blocks we deployed earlier:
    
    $regexDualImgs = '(?s)<!-- Primary Logo for Light Contexts \(Hidden in Dark Navbar\) -->.*?<img class="ea-logo block dark:hidden".*?>'
    
    $content = $content -replace $regexDualImgs, $singleLogoNavbar
    
    # Also standardize the explicit 48px size in login screens to use the exact same logic (no filter needed coz it's on white bg)
    # The login screens are: users/login.html, organizers/login.html, coordinators/login.html
    # Some have class="ea-logo", some "ea-logo mx-auto", etc.
    # Let's just blindly force any explicit img tag that calls eventaxis-logo.png to have standard sizing if not in navbar:
    
    if ($content -ne $original) {
        Set-Content $_.FullName -Value $content -NoNewline
        Write-Host "Refactored to SINGLE-SOURCE architecture -> " $_.FullName
    }
}
