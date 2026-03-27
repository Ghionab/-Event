$path = "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\templates"
$results = @()

Get-ChildItem -Path $path -Recurse -Filter *.html | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $issues = @()
    
    # 1. Raw layout/card patterns missing .ea-card
    if ($content -match 'class="[^"]*bg-white\s+shadow(-[a-z]+)?\s+rounded(-[a-z]+)?[^"]*"') {
        if (-not ($content -match 'ea-card')) {
            $issues += "Raw Tailwind card (missing ea-card)"
        }
    }
    
    # 2. Raw button patterns missing .ea-btn
    if ($content -match 'class="[^"]*bg-(blue|indigo|purple|green|primary)-\d+\s+text-white\s+px-\d+\s+py-\d+[^"]*"') {
         if (-not ($content -match 'ea-btn')) {
             $issues += "Raw Tailwind button (missing ea-btn)"
         }
    }
    if ($content -match 'class="[^"]*bg-primary\s+text-white\s+px-\d+\s+py-\d+[^"]*"') {
         if (-not ($content -match 'ea-btn')) {
             $issues += "Raw primary button (missing ea-btn)"
         }
    }

    # 3. Old Tailwind colors instead of semantic colors
    if ($content -match 'bg-indigo-') { $issues += "Uses old brand color (indigo)" }
    if ($content -match 'bg-blue-600' -or $content -match 'text-blue-600') { $issues += "Uses generic blue instead of primary/accent" }
    
    # 4. Inconsistent Typography (missing font-heading on h1-h4) - Note: We added global h1-h4 rule, but let's check for explicit wrong fonts or missing ea-page-header
    
    # 5. Font Awesome usage (should be 0, but checking again just in case)
    if ($content -match 'fas fa-' -or $content -match 'far fa-') { $issues += "Font Awesome used (should be Bootstrap Icons)" }

    # 6. Check for Tailwind CDN in non-base files
    if ($content -match 'cdn.tailwindcss.com' -and $_.Name -ne 'base.html' -and $_.Name -ne '404.html' -and $_.Name -ne '500.html') {
        $issues += "Tailwind CDN included in sub-template"
    }

    # Decide status
    $status = "✅"
    if ($issues.Count -gt 0 -and $issues.Count -le 2) { $status = "⚠️" }
    elseif ($issues.Count -gt 2) { $status = "❌" }
    
    if ($issues.Count -gt 0) {
        $results += [PSCustomObject]@{
            File = $_.FullName.Replace("c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\templates\", "")
            Status = $status
            Issues = ($issues -join "; ")
        }
    } else {
        $results += [PSCustomObject]@{
            File = $_.FullName.Replace("c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\templates\", "")
            Status = "✅"
            Issues = "None"
        }
    }
}

$results | ConvertTo-Json -Depth 3 | Out-File -FilePath "c:\Users\zefasil\Desktop\cloning to test and work my part\Intern-project\audit_results.json"
Write-Host "Audit complete. Results saved to audit_results.json"
