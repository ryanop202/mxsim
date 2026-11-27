# maj_paris.ps1 - fabrique la piste de Paris (version Zion, USLANDParis) et la met dans MX Simulator.
#
# Lance tout seul apres chaque "git pull" (hook .githooks/post-merge) une fois active avec :
#     git config core.hooksPath .githooks
# ou a la main, depuis la racine du depot :
#     powershell -NoProfile -ExecutionPolicy Bypass -File commun/tools/maj_paris.ps1
#
# Etapes : 1. stade (stade_paris/src/build.py --mx, pas sur GitHub)  2. piste construite dans un dossier temporaire
# (build_zion.py --out, le depot reste propre pour le prochain pull)  3. copie de USLANDParis + USLAND2026SX1 (textures
# partagees) dans le dossier des pistes de MX Simulator.
# Dossier du jeu : -MxDir ou variable MXSIM_DIR, sinon celui qui contient deja USLANDParis ou JGSX2026Scuttle.
param([string]$MxDir = $env:MXSIM_DIR, [switch]$SansStade, [switch]$SansPip)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
$Log = Join-Path $env:TEMP "maj_paris.log"
"=== maj_paris $(Get-Date -Format s) ===" | Out-File $Log -Encoding utf8

function Write-Etape($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan; "== $t" | Out-File $Log -Append -Encoding utf8 }

$env:PYTHONIOENCODING = "utf-8"; [Console]::OutputEncoding = [Text.Encoding]::UTF8

function Invoke-Py {
    param([string[]]$PyArgs)
    # python ecrit des avertissements sur stderr : on ne s'arrete que sur son code de sortie
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & $script:Py @script:PyPre @PyArgs 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; $l | Out-File $Log -Append -Encoding utf8 }
    $code = $LASTEXITCODE; $ErrorActionPreference = $old
    if ($code -ne 0) { throw "echec : python $($PyArgs -join ' ') (journal : $Log)" }
}

# ---- python
$script:Py = $null; $script:PyPre = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) { $script:Py = "py"; $script:PyPre = @("-3.12") }
}
if (-not $script:Py) {
    if (Get-Command python -ErrorAction SilentlyContinue) { $script:Py = "python" }
    else { throw "Python 3.12 introuvable (installer Python 3.12 puis relancer)" }
}

# ---- dossier des pistes de MX Simulator
$cands = @($MxDir, (Join-Path $env:LOCALAPPDATA "MX Simulator"), "${env:ProgramFiles(x86)}\MX Simulator", "$env:ProgramFiles\MX Simulator") |
    Where-Object { $_ -and (Test-Path $_) }
$Game = $cands | Where-Object { Test-Path (Join-Path $_ "USLANDParis") } | Select-Object -First 1
if (-not $Game) { $Game = $cands | Where-Object { Test-Path (Join-Path $_ "JGSX2026Scuttle") } | Select-Object -First 1 }
if (-not $Game) { $Game = $cands | Select-Object -First 1 }
if (-not $Game) { throw "dossier de MX Simulator introuvable : relancer avec -MxDir ""C:\chemin\vers\MX Simulator""" }
Write-Host "MX Simulator : $Game"

try {
    if (-not $SansPip) { Write-Etape "0/3 modules python"
    Invoke-Py @("-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r", "requirements.txt") }

    if (-not $SansStade) {
        Write-Etape "1/3 stade (Paris La Defense Arena)"
        Invoke-Py @("-I", "pistes/paris-2026/stade_paris/src/build.py", "--mx")
    }

    Write-Etape "2/3 piste USLANDParis (dossier temporaire)"
    $Tmp = Join-Path $env:TEMP "mxsim_paris"
    $Out = Join-Path $Tmp "USLANDParis"
    New-Item -ItemType Directory -Force $Tmp | Out-Null
    robocopy (Join-Path $Repo "tracks\USLANDParis") $Out /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "copie de tracks\USLANDParis impossible" }
    $env:PARIS_ZION = "1"
    Invoke-Py @("pistes/paris-2026/build_zion.py", "--out", $Out)

    Write-Etape "3/3 copie dans le jeu"
    foreach ($p in @(@($Out, (Join-Path $Game "USLANDParis")), @((Join-Path $Repo "tracks\USLAND2026SX1"), (Join-Path $Game "USLAND2026SX1")))) {
        robocopy $p[0] $p[1] /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "copie vers $($p[1]) impossible (droits ? fermer le jeu, ou -MxDir vers le dossier perso)" }
        Write-Host "  -> $($p[1])"
    }
    Write-Host ""
    Write-Host "Paris (USLANDParis) a jour dans MX Simulator - non teste en jeu. Journal : $Log" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "ECHEC : $_" -ForegroundColor Red
    Write-Host "Journal : $Log"
    exit 1
}
