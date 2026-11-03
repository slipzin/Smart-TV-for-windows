# Unit tests for TvMap (the controller's decisions in tv.ps1), without Windows.
$ErrorActionPreference = 'Stop'
$src = Get-Content (Join-Path $PSScriptRoot '..\tv.ps1') -Raw
$codigo = [regex]::Match($src, "(?s)\`$CodigoControle = @'\r?\n(.*?)\r?\n'@").Groups[1].Value
if (-not $codigo) { throw 'C# block not found in tv.ps1' }
Add-Type -TypeDefinition $codigo
$falhas = 0
function Confere($nome, $esperado, $obtido) {
  $e = ($esperado -join ','); $o = ($obtido -join ',')
  if ($e -ne $o) { Write-Host "FALHOU: $nome`n  esperado: [$e]`n  obtido:   [$o]"; $script:falhas++ } else { Write-Host "ok: $nome" }
}
function Passos($m, $passos, $ativo = $true) {
  $out = @()
  foreach ($p in $passos) { $out += @($m.Step($p[0], 0, 0, $p[1], $p[2], $p[3], $p[4], $ativo)) }
  return $out
}
$VIEW = 0x20; $MENU = 0x10

# Exit combo: View + Menu held 1.5 s, once, and no Alt+F4 when they are let go (either order)
$m = New-Object TvMap
$r = Passos $m @(@($VIEW,0,0,0,0), @(($VIEW -bor $MENU),0,0,0,100), @(($VIEW -bor $MENU),0,0,0,900), @(($VIEW -bor $MENU),0,0,0,1700), @(($VIEW -bor $MENU),0,0,0,1800), @($VIEW,0,0,0,1900), @(0,0,0,0,2000))
Confere 'exit combo fires once, nothing else' @('EXIT') $r
$m = New-Object TvMap
$r = Passos $m @(@($MENU,0,0,0,0), @(($VIEW -bor $MENU),0,0,0,10), @($MENU,0,0,0,300), @(0,0,0,0,400))
Confere 'combo let go early: no exit, no Alt+F4' @() $r
# View on its own closes the app
$m = New-Object TvMap
Confere 'View alone: Alt+F4' @('C:18:115') (Passos $m @(@($VIEW,0,0,0,0), @(0,0,0,0,80)))
$m = New-Object TvMap
Confere 'View alone outside a media app: nothing' @() (Passos $m @(@($VIEW,0,0,0,0), @(0,0,0,0,80)) $false)
# Other buttons press no keys (the apps read the controller themselves)
$m = New-Object TvMap
Confere 'A, B, X, Y, D-pad, LB, RB: no keys' @() (Passos $m @(@(0x1000,0,0,0,0), @(0,0,0,0,50), @(0x2000,0,0,0,100), @(0x4000,0,0,0,150), @(0x8000,0,0,0,200), @(0x1,0,0,0,250), @(0x300,0,0,0,300), @(0,0,0,0,350)))
# Right stick = mouse, RT = click; a click is let go when the app loses the focus
$m = New-Object TvMap
Confere 'right stick moves the mouse' @('M:10:-5') (Passos $m @(,@(0, 18000, 9000, 0, 0)))
Confere 'dead zone: no move' @() (Passos $m @(,@(0, 5000, -7000, 0, 20)))
$m = New-Object TvMap
Confere 'RT: press and release' @('D','U') (Passos $m @(@(0,0,0,200,0), @(0,0,0,250,16), @(0,0,0,10,32)))
$m = New-Object TvMap
$r = @(Passos $m @(,@(0,0,0,200,0))) + @(Passos $m @(,@(0,0,0,200,16)) $false)
Confere 'RT held when the focus leaves: released' @('D','U') $r
# Where it helps
foreach ($n in 'ApplicationFrameHost', 'Spotify', 'vlc', 'Plex HTPC') { Confere "media app: $n" @($true) @([TvMap]::MediaApp($n)) }
foreach ($n in 'msedge', 'cod', 'steam', 'explorer', '', $null) { Confere "not a media app: '$n'" @($false) @([TvMap]::MediaApp($n)) }
if ($falhas) { Write-Host "$falhas falha(s)"; exit 1 }
Write-Host 'TvMap: todos os testes passaram'
