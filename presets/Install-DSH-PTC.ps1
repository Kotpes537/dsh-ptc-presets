#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess)]
param([string]$ProfileDir)

$ErrorActionPreference = 'Stop'
if (-not $ProfileDir) {
    $dshRoot = if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE '.dsh' }
    $ProfileDir = Join-Path $dshRoot 'profiles/desktop'
}
$ProfileDir = (Resolve-Path -LiteralPath $ProfileDir).ProviderPath
if (-not (Test-Path -LiteralPath $ProfileDir -PathType Container)) {
    throw 'The target DSH profile directory must already exist.'
}

$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$installerName = 'Install-DSH-PTC.ps1'
$templateName = 'ptc.patch.yml.in'
$pluginFiles = @()
foreach ($entry in $manifest.files) {
    $relative = [string]$entry.path
    if ($relative -ne $installerName -and $relative -ne $templateName -and
        $relative -notmatch '^local-plugins/ptc-(?:astra|workflow)/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*\.(?:md|mjs)$') {
        throw "Unexpected archive member: $relative"
    }
    $source = Join-Path $PSScriptRoot $relative
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry.sha256) {
        throw "Hash mismatch: $relative"
    }
    if ($relative.StartsWith('local-plugins/')) {
        $destination = Join-Path $ProfileDir $relative
        if (Test-Path -LiteralPath $destination) {
            if (-not (Test-Path -LiteralPath $destination -PathType Leaf) -or
                (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $entry.sha256) {
                throw "Existing plugin file differs. Review it before migrating: $destination"
            }
        }
        $pluginFiles += [pscustomobject]@{ Source = $source; Destination = $destination }
    }
}

$start = '# BEGIN PORTABLE DSH PTC'
$end = '# END PORTABLE DSH PTC'
$patch = Join-Path $ProfileDir 'cordis.patch.yml'
$original = if (Test-Path -LiteralPath $patch) { [IO.File]::ReadAllText($patch) } else { '' }
$profilePath = $ProfileDir.Replace('\', '/').TrimEnd('/')
$profileUri = ([Uri]($ProfileDir.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar)).AbsoluteUri.TrimEnd('/')
$template = Get-Content -LiteralPath (Join-Path $PSScriptRoot $templateName) -Raw -Encoding UTF8
$payload = $template.Replace('__DSH_PROFILE_URI__', $profileUri).Replace('__DSH_PROFILE_PATH__', $profilePath)
$newline = [Environment]::NewLine
$block = $start + $newline + $payload.TrimEnd() + $newline + $end
$existingBlock = [regex]::Match($original, '(?ms)^# BEGIN PORTABLE DSH PTC\r?\n.*?^# END PORTABLE DSH PTC[ \t]*(?=\r?$)')
$existingPtc = '(?m)^\s*-\s+id:\s*(?:preset-ptc-(?:astra|workflow(?:-[a-z0-9-]+)?)|ptc-model-delegation-budget)\s*(?:#.*)?$'

if ($existingBlock.Success) {
    $base = $original.Remove($existingBlock.Index, $existingBlock.Length)
    if ($base -match $existingPtc -or $base.Contains($start) -or $base.Contains($end)) {
        throw 'The profile also contains a separate PTC declaration.'
    }
    $next = $original
    $oldBlock = $existingBlock.Value.Replace([string][char]13, '')
    $newBlock = $block.Replace([string][char]13, '')
    if ($oldBlock -cne $newBlock) {
        $teamLine = '(?m)^ {18}allowedAgentPresets: \[ ptc-workflow-review(?:, ptc-workflow-[a-z0-9-]+)* \](?=\r?$)'
        $oldTeam = [regex]::Matches($existingBlock.Value, $teamLine)
        $newTeam = [regex]::Matches($block, $teamLine)
        $stripTeam = $teamLine + '\r?\n'
        if ($oldTeam.Count -notin @(1, 2) -or $newTeam.Count -ne 2 -or
            [regex]::Replace($oldBlock, $stripTeam, '') -cne [regex]::Replace($newBlock, $stripTeam, '')) {
            throw 'The existing portable PTC block differs outside the subagent allowlist. Review it before migrating.'
        }
        $next = $original.Remove($existingBlock.Index, $existingBlock.Length).Insert($existingBlock.Index, $block)
    }
} else {
    if ($original -match $existingPtc -or $original.Contains($start) -or $original.Contains($end)) {
        throw 'PTC is already declared in the target profile. Review the existing block before merging.'
    }
    $base = $original
    if ($base.Trim() -eq '[]') {
        $base = ''
    }
    $body = $base -replace '(?m)^#[^\r\n]*\r?\n', ''
    if ($body.Trim() -and ($body.TrimStart() -notmatch '^-\s' -or $body -match '(?m)^(?:---|\.\.\.)\s*$')) {
        throw 'The target patch is not a single YAML block sequence. Merge the PTC patch manually.'
    }
    $separator = if ($base.Length -eq 0) { '' } elseif ($base.EndsWith([string][char]10)) { $newline } else { $newline + $newline }
    $next = $base + $separator + $block + $newline
}

if (-not $PSCmdlet.ShouldProcess($ProfileDir, 'Install PTC plugin files and append the preset patch')) { return }
foreach ($file in $pluginFiles) {
    if (-not (Test-Path -LiteralPath $file.Destination)) {
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($file.Destination))
        [IO.File]::Copy($file.Source, $file.Destination)
    }
}
if ($next -cne $original) {
    $temp = Join-Path $ProfileDir ('.ptc-' + [guid]::NewGuid().ToString('n') + '.tmp')
    try {
        [IO.File]::WriteAllText($temp, $next, [Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $patch) {
            if ([IO.File]::ReadAllText($patch) -cne $original) {
                throw "The target patch changed during installation: $patch"
            }
            $backup = $patch + '.pre-ptc-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
            [IO.File]::Replace($temp, $patch, $backup)
            Write-Output "Backup: $backup"
        } else {
            [IO.File]::Move($temp, $patch)
        }
    } finally {
        if (Test-Path -LiteralPath $temp) { [IO.File]::Delete($temp) }
    }
}
Write-Output "PTC installed in $ProfileDir. Open a new session after restarting DSH."
