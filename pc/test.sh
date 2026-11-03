#!/usr/bin/env bash
# Tests the Windows package without Windows: PowerShell 5.1 compatibility, the controller code as C# 5 (what
# Windows PowerShell compiles), the controller's decisions, the real tv.ps1 in test mode against a pretend PC, and
# the home screen in Chromium driven by a pretend game controller (screen sizes, buttons, a long run).
#   pc/test.sh [minutes of the long run, default 3]
# Needs pwsh and python3; uses PSScriptAnalyzer, mcs (Mono) and Node with Playwright when they are there.
set -euo pipefail
cd "$(dirname "$0")/.."
PWSH="${PWSH:-$(command -v pwsh || echo /opt/pwsh/pwsh)}"
export PWSH
OUT=out/pc
python3 -I pc/build.py --out "$OUT/SmartTV"

echo "== PowerShell 5.1 (Windows 10/11) =="
"$PWSH" -NoProfile -Command '
$e = $null; [System.Management.Automation.Language.Parser]::ParseFile("pc/tv.ps1", [ref]$null, [ref]$e) | Out-Null
if ($e) { $e; exit 1 }
if (-not (Get-Module -ListAvailable PSScriptAnalyzer)) { "PSScriptAnalyzer not installed: compatibility not checked"; exit 0 }
$dir = Join-Path (Split-Path (Get-Module -ListAvailable PSScriptAnalyzer | Select-Object -First 1).Path) "compatibility_profiles"
$prof = Get-ChildItem $dir | Where-Object Name -match "win-.*_5\.1\." | Select-Object -ExpandProperty BaseName
$s = @{ Rules = @{ PSUseCompatibleSyntax = @{ Enable = $true; TargetVersions = @("5.1") }
                   PSUseCompatibleCommands = @{ Enable = $true; TargetProfiles = $prof }
                   PSUseCompatibleTypes = @{ Enable = $true; TargetProfiles = $prof } } }
$r = @(Invoke-ScriptAnalyzer -Path pc/tv.ps1 -Settings $s | Where-Object RuleName -like "PSUseCompatible*")
$r += @(Invoke-ScriptAnalyzer -Path pc/tv.ps1 -Severity Error)
if ($r.Count) { $r | Format-Table RuleName, Line, Message -AutoSize -Wrap | Out-String -Width 200; exit 1 }
"ok: compatible with Windows PowerShell 5.1 (" + $prof.Count + " Windows profiles)"'

echo "== C# 5 =="
if command -v mcs >/dev/null; then
  tmp="$(mktemp -d)"
  python3 -I -c "import re,sys;s=open('pc/tv.ps1',encoding='utf-8').read();m=re.search(r\"\\\$CodigoControle = @'\r?\n(.*?)\r?\n'@\",s,re.S);open(sys.argv[1],'w').write(m.group(1))" "$tmp/c.cs"
  mcs -langversion:5 -target:library -out:"$tmp/c.dll" "$tmp/c.cs" && echo "ok: the controller code compiles as C# 5"
  rm -rf "$tmp"
else
  echo "mcs not installed: C# 5 not checked"
fi

echo "== controller =="
"$PWSH" -NoProfile -File pc/test/map.ps1 | tail -1

echo "== server =="
python3 -I pc/test/servidor.py "$OUT/SmartTV"

echo "== home screen =="
if command -v node >/dev/null && NODE_PATH="$(npm root -g)" node -e "require('playwright')" 2>/dev/null; then
  NODE_PATH="$(npm root -g)" node pc/test/tela.js "$OUT/SmartTV" "$OUT/telas" "${1:-3}"
else
  echo "Node with Playwright not found: the home screen not checked"
fi
echo "All Windows checks passed."
