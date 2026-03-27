$basePath = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project"
$results = @()

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'media', 'static', 'advanced - Copy')

Get-ChildItem -Path $basePath -Recurse -Filter *.html | Where-Object {
    $path = $_.FullName
    $skip = $false
    foreach ($dir in $excludeDirs) {
        if ($path -match "\\$dir\\") { $skip = $true; break }
    }
    # Skip the ones we just fixed perfectly
    # Actually, let's scan EVERYTHING so we have ONE source of truth, but we know templates/participant is clean now.
    if ($path -match "templates\\participant" -or $path -match "templates\\registration" -or $path -match "templates\\404" -or $path -match "templates\\500" -or $path -match "templates\\base") {
        # $skip = $true 
        # Actually I want to include them to show they are ✅!
    }
    -not $skip
} | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $issues = @()
    
    # 1. Raw cards
    if ($content -match 'class="[^"]*bg-white\s+shadow(-[a-z]+)?\s+rounded(-[a-z]+)?[^"]*"') {
        if (-not ($content -match 'ea-card')) {
            $issues += "Raw Tailwind card (missing ea-card)"
        }
    }
    
    # 2. Raw buttons
    if ($content -match 'class="[^"]*bg-(blue|indigo|purple|green|primary)-\d+\s+text-white\s+px-\d+\s+py-\d+[^"]*"') {
         if (-not ($content -match 'ea-btn')) {
             $issues += "Raw Tailwind button (missing ea-btn)"
         }
    }

    # 3. Colors
    if ($content -match 'bg-indigo-') { $issues += "Uses old brand color (indigo)" }
    if ($content -match 'text-indigo-') { $issues += "Uses old brand color (indigo text)" }
    if ($content -match 'bg-blue-600' -or $content -match 'text-blue-600') { $issues += "Uses generic blue instead of primary/accent" }
    
    # 4. Font Awesome
    if ($content -match 'fas fa-' -or $content -match 'far fa-') { $issues += "Font Awesome used (should be Bootstrap Icons)" }

    # 5. CDNs
    if ($content -match 'cdn.tailwindcss.com' -and $_.Name -ne 'base.html') {
        $issues += "Tailwind CDN included in sub-template"
    }

    $status = "✅"
    if ($issues.Count -gt 0 -and $issues.Count -le 2) { $status = "⚠️" }
    elseif ($issues.Count -gt 2) { $status = "❌" }
    
    $relativeName = $_.FullName.Substring($basePath.Length + 1)
    
    if ($issues.Count -gt 0) {
        $results += [PSCustomObject]@{
            File = $relativeName
            Status = $status
            Issues = ($issues -join "; ")
        }
    } else {
        $results += [PSCustomObject]@{
            File = $relativeName
            Status = "✅"
            Issues = "None"
        }
    }
}

$results | ConvertTo-Json -Depth 3 | Out-File -FilePath "$basePath\audit_all_apps.json"
Write-Host "Audit complete. Results saved to audit_all_apps.json"
