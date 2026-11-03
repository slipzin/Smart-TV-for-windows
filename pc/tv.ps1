# ============================================================
#  Smart TV para Windows: a tela inicial de TV em tela cheia.
#  Aberto pelo INICIAR-TV.bat (no pendrive). Nao instala nada e nao muda o Windows:
#  serve a tela num endereco so deste PC (127.0.0.1:48765), abre o Edge em modo
#  quiosque e abre os aplicativos instalados no PC (Netflix, Prime Video, Spotify, Steam, Xbox...).
#  Sair do modo TV: segure View + Menu no controle (ou Alt+F4).
#
#  -Teste <pasta>: modo de teste (pc/test.sh). Nada e aberto de verdade: o que seria aberto
#  e anotado em <pasta>\abertos.txt, e um arquivo <pasta>\sair encerra o modo TV.
# ============================================================
param([string]$Teste = '')
$ErrorActionPreference = 'Continue'
$Raiz  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Web   = Join-Path $Raiz 'web'
$Porta = 48765
$Base  = "http://127.0.0.1:$Porta/"
$Dados = if ($Teste) { $Teste } else { Join-Path $env:LOCALAPPDATA 'SmartTV' }   # logins e ajustes: neste PC
New-Item -ItemType Directory -Force -Path $Dados | Out-Null
$Log = Join-Path $Dados 'tv.log'
function Log($m) { try { Add-Content -Path $Log -Value ('{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $m) } catch {} }
Log 'inicio'

function Avisar($m) {
  Log "aviso: $m"
  if ($Teste) { return }
  try {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($m, 'Smart TV') | Out-Null
  } catch {}
}

# Tudo o que o modo TV abre passa por aqui (no teste, so e anotado).
function Abrir($alvo, [string[]]$argumentos) {
  if ($Teste) {
    Add-Content -Path (Join-Path $Teste 'abertos.txt') -Value ($alvo + ' | ' + ($argumentos -join ' | '))
    return
  }
  if ($argumentos -and $argumentos.Count) { Start-Process $alvo -ArgumentList $argumentos }
  else { Start-Process $alvo }
}

# ---------- Navegador (Edge vem em todo Windows 10/11; Chrome se nao houver) ----------
function AcharNavegador {
  if ($Teste) { return 'navegador' }
  $lista = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")
  foreach ($c in $lista) { if ($c -and (Test-Path $c)) { return $c } }
  return $null
}
$Navegador = AcharNavegador
if (-not $Navegador) { Avisar 'Nao achei o Microsoft Edge nem o Google Chrome neste PC.'; exit 1 }

$ArgsTela = @("--user-data-dir=`"$Dados\home`"", '--kiosk', $Base, '--edge-kiosk-type=fullscreen', '--no-first-run',
              '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required', '--disable-features=Translate')

# ---------- Ja esta aberto? So traz a tela de volta ----------
$jaAberto = $false
try {
  $sonda = New-Object System.Net.Sockets.TcpClient
  $sonda.Connect('127.0.0.1', $Porta)
  $sonda.Close()
  $jaAberto = $true
} catch {}
if ($jaAberto) { Log 'ja estava aberto: so a tela'; Abrir $Navegador $ArgsTela; exit 0 }

# ---------- Steam, lojas e apps instalados ----------
function SteamExe {
  $p = $null
  if ($Teste) {
    $f = Join-Path $Teste 'steam.txt'
    if (Test-Path $f) { $p = (Get-Content $f -Raw).Trim() }
  } else {
    $p = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamExe
  }
  if ($p) { $p = $p -replace '/', [string][System.IO.Path]::DirectorySeparatorChar }
  if ($p -and (Test-Path $p)) { return $p }
  return $null
}
function SteamTemJogo($appid) {
  $steam = SteamExe
  if (-not $steam) { return $false }
  $pastas = @(Split-Path $steam)
  $vdf = Join-Path (Join-Path (Split-Path $steam) 'steamapps') 'libraryfolders.vdf'
  if (Test-Path $vdf) {
    foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
      $pastas += ($m.Groups[1].Value -replace '\\\\', '\')
    }
  }
  foreach ($p in $pastas) {
    if (Test-Path (Join-Path (Join-Path $p 'steamapps') "appmanifest_$appid.acf")) { return $true }
  }
  return $false
}
$AppsDoMenu = $null
function AppDaLoja($nome) {
  if ($null -eq $script:AppsDoMenu) {
    $script:AppsDoMenu = @()
    if ($Teste) {
      $f = Join-Path $Teste 'startapps.json'
      if (Test-Path $f) { try { $script:AppsDoMenu = @(Get-Content $f -Raw | ConvertFrom-Json) } catch {} }
    } else {
      try { $script:AppsDoMenu = @(Get-StartApps) } catch {}
    }
  }
  $a = $script:AppsDoMenu | Where-Object { $_.Name -match $nome -and -not (EhSite $_.AppID) } | Select-Object -First 1
  if ($a) { return $a.AppID }
  return $null
}

# Os apps da tela: so aplicativos instalados no Windows, como numa smart TV (nada aberto pelo navegador).
# Cada um e procurado na lista de apps do menu Iniciar (Microsoft Store e programas) e aberto por ela.
# Atalhos que o Edge ou o Chrome criam para sites ("instalar este site como app") ficam de fora.
# id: o mesmo dos apps da TV, para os destaques do TMDB acharem o app certo (data.js, SERVICES).
$Conhecidos = @(
  @{ id = 'netflix'; title = 'Netflix'; color = '#E50914'; icon = 'icons/netflix.svg'; nome = '^Netflix$' },
  @{ id = 'amazon'; title = 'Prime Video'; color = '#1A98FF'; icon = 'icons/prime.png'; nome = '^(Amazon )?Prime Video' },
  @{ id = 'disney'; title = 'Disney+'; color = '#1838C8'; icon = ''; nome = '^Disney' },
  @{ id = 'hbo.max'; title = 'HBO Max'; color = '#6C3BE0'; icon = 'icons/max.svg'; nome = '^(HBO )?Max$|^HBO Max' },
  @{ id = 'globoplay'; title = 'Globoplay'; color = '#FF5A1F'; icon = ''; nome = '^Globoplay' },
  @{ id = 'appletv'; title = 'Apple TV'; color = '#B8BCC6'; icon = 'icons/appletv.svg'; nome = '^Apple TV' },
  @{ id = 'youtube.leanback.v4'; title = 'YouTube'; color = '#FF0033'; icon = 'icons/youtube.png'; nome = '^YouTube$' },
  @{ id = 'crunchyroll'; title = 'Crunchyroll'; color = '#F47521'; icon = 'icons/crunchyroll.svg'; nome = '^Crunchyroll' },
  @{ id = 'twitch'; title = 'Twitch'; color = '#9146FF'; icon = 'icons/twitch.svg'; nome = '^Twitch$' },
  @{ id = 'spotify'; title = 'Spotify'; color = '#1DB954'; icon = 'icons/spotify.svg'; nome = '^Spotify' },
  @{ id = 'deezer'; title = 'Deezer'; color = '#A238FF'; icon = 'icons/deezer.svg'; nome = '^Deezer' },
  @{ id = 'plex'; title = 'Plex'; color = '#E5A00D'; icon = 'icons/plex.svg'; nome = '^Plex( HTPC)?$' },
  @{ id = 'jellyfin'; title = 'Jellyfin'; color = '#AA5CC3'; icon = 'icons/jellyfin.svg'; nome = '^Jellyfin' },
  @{ id = 'vlc'; title = 'VLC'; color = '#FF8800'; icon = ''; nome = '^VLC media player$' },
  @{ id = 'kodi'; title = 'Kodi'; color = '#17B2E7'; icon = ''; nome = '^Kodi$' },
  @{ id = 'xbox'; title = 'Xbox'; color = '#107C10'; icon = ''; nome = '^Xbox$' },
  @{ id = 'battlenet'; title = 'Battle.net'; color = '#148EFF'; icon = ''; nome = '^Battle\.net$' },
  @{ id = 'epic'; title = 'Epic Games'; color = '#2A2A2A'; icon = ''; nome = '^Epic Games Launcher$' }
)
# Atalhos de sites: os do Edge e do Chrome ("_crx_"), e os de endereco da web
function EhSite($appId) { return [bool]($appId -match '_crx_|^MSEdge\.|^Chrome\.|^https?://') }

function Catalogo {
  $out = New-Object System.Collections.ArrayList
  foreach ($k in $Conhecidos) {
    $aid = AppDaLoja $k.nome
    if ($aid) {
      [void]$out.Add(@{ id = $k.id; title = $k.title; color = $k.color; icon = $k.icon; kind = 'start'; target = $aid })
    } elseif ($k.id -eq 'spotify' -and $env:APPDATA -and (Test-Path (Join-Path $env:APPDATA 'Spotify\Spotify.exe'))) {
      [void]$out.Add(@{ id = 'spotify'; title = 'Spotify'; color = $k.color; icon = $k.icon; kind = 'exe'; target = (Join-Path $env:APPDATA 'Spotify\Spotify.exe') })
    }
  }
  # Steam: o modo Big Picture, que e a "tela de TV" da propria Steam, e o Call of Duty dela
  if (SteamExe) {
    [void]$out.Add(@{ id = 'steam'; title = 'Steam'; color = '#1B2838'; icon = 'icons/steam.svg'; kind = 'url'; target = 'steam://open/bigpicture' })
    if (SteamTemJogo 1938090) { [void]$out.Add(@{ id = 'cod'; title = 'Call of Duty'; color = '#2B2B2B'; icon = ''; kind = 'url'; target = 'steam://rungameid/1938090' }) }
  }
  return $out
}
$Apps = Catalogo
Log ("apps: " + (($Apps | ForEach-Object { $_.id }) -join ', '))

function AbrirApp($id) {
  $a = $Apps | Where-Object { $_.id -eq $id } | Select-Object -First 1
  if (-not $a) { Log "app desconhecido: $id"; return $false }
  try {
    switch ($a.kind) {
      'start' { Abrir "shell:AppsFolder\$($a.target)" @() }
      'exe'   { Abrir $a.target @() }
      'url'   { Abrir $a.target @() }
    }
    Log "abriu $id"
    return $true
  } catch { Log "erro ao abrir $id : $_"; return $false }
}

# ---------- Controle de Xbox nos apps ----------
# A tela inicial le o controle sozinha (Gamepad API: Xbox, PlayStation...), e os apps da Store (Netflix, Prime
# Video...) leem o de Xbox sozinhos. Este leitor (XInput) so completa: o analogico direito vira mouse e o RT clica
# (para os apps feitos para mouse, como o Spotify), e View fecha o app e volta para a tela inicial. So nos apps de
# midia (TvMap.MediaApp), nunca dentro de um jogo, nunca com a Steam aberta (ela tem o "layout de desktop").
# TvMap decide (sem tocar no Windows, testado em pc/test.sh); TvPad le o controle e aperta as teclas.
$CodigoControle = @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

public class TvMap {
    // XInput buttons
    public const int UP = 0x1, DOWN = 0x2, LEFT = 0x4, RIGHT = 0x8, MENU = 0x10, VIEW = 0x20,
        LB = 0x100, RB = 0x200, A = 0x1000, B = 0x2000, X = 0x4000, Y = 0x8000;
    // What a step asks for: "K:<vk>" a key, "C:<mod>:<vk>" a chord, "M:<dx>:<dy>" mouse move, "D"/"U" left button, "EXIT".
    int prev;
    long comboSince;
    bool rtDown, chord;   // chord: View and Menu were down together since one of them went down
    public bool Exit;

    // The windows it helps in: Store apps (they run in ApplicationFrameHost) and the media apps of the home screen.
    // Never a game, never the home screen (msedge), never Steam.
    static readonly string[] MEDIA = { "applicationframehost", "spotify", "netflix", "primevideo", "disneyplus", "appletv",
        "deezer", "plex", "plex htpc", "jellyfin media player", "jellyfinmediaplayer", "vlc", "kodi" };
    public static bool MediaApp(string process) {
        string n = (process ?? "").ToLowerInvariant();
        return Array.IndexOf(MEDIA, n) >= 0;
    }

    public List<string> Step(int b, int lx, int ly, int rx, int ry, int rt, long now, bool active) {
        List<string> o = new List<string>();
        // View + Menu held 1.5 s: leave TV mode (anywhere, even in the home screen)
        if ((b & (VIEW | MENU)) == (VIEW | MENU)) {
            chord = true;
            if (comboSince == 0) comboSince = now;
            else if (now - comboSince > 1500 && !Exit) { Exit = true; o.Add("EXIT"); }
        } else comboSince = 0;
        int released = prev & ~b;
        bool wasChord = chord;
        if ((b & (VIEW | MENU)) == 0) chord = false;
        if (!active) {
            if (rtDown) { o.Add("U"); rtDown = false; }
            prev = b;
            return o;
        }
        // The apps read the controller themselves (Netflix, Prime Video...: Xbox controllers): no keys are pressed
        // for them, or each button would act twice. Only what they lack: a mouse for the ones made for one
        // (Spotify...), and a way back to the home screen.
        if ((released & VIEW) != 0 && !wasChord) o.Add("C:18:115");   // View on its own: closes the app (Alt+F4), back home
        int mx = Math.Abs(rx) > 8000 ? rx / 1800 : 0, my = Math.Abs(ry) > 8000 ? -ry / 1800 : 0;
        if (mx != 0 || my != 0) o.Add("M:" + mx + ":" + my);
        bool rtNow = rt > 150;
        if (rtNow && !rtDown) o.Add("D");
        if (!rtNow && rtDown) o.Add("U");
        rtDown = rtNow;
        prev = b;
        return o;
    }
}

public static class TvPad {
    [StructLayout(LayoutKind.Sequential)] public struct GP { public ushort b; public byte lt, rt; public short lx, ly, rx, ry; }
    [StructLayout(LayoutKind.Sequential)] public struct ST { public uint pkt; public GP g; }
    [DllImport("xinput1_4.dll")] static extern int XInputGetState(int i, out ST s);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte sc, uint fl, UIntPtr ex);
    [DllImport("user32.dll")] static extern void mouse_event(uint fl, int dx, int dy, uint data, UIntPtr ex);

    public static volatile bool Exit;
    public static volatile bool Running;
    static readonly TvMap map = new TvMap();
    static bool apps, steam;
    static long checkedAt = -1000, steamAt = -5000;

    public static void Start() {
        Thread t = new Thread(Loop);
        t.IsBackground = true;
        t.Start();
    }

    static void Loop() {
        Running = true;
        try { Run(); } catch (Exception) { }   // sem XInput (Windows antigo): a tela inicial ainda le o controle sozinha
        Running = false;
    }

    static void Key(byte vk, bool up) { keybd_event(vk, 0, up ? 2u : 0u, UIntPtr.Zero); }

    static void Do(string a) {
        string[] p = a.Split(':');
        if (p[0] == "K") { byte vk = byte.Parse(p[1]); Key(vk, false); Key(vk, true); }
        else if (p[0] == "C") { byte m = byte.Parse(p[1]), vk = byte.Parse(p[2]); Key(m, false); Key(vk, false); Key(vk, true); Key(m, true); }
        else if (p[0] == "M") mouse_event(0x0001, int.Parse(p[1]), int.Parse(p[2]), 0, UIntPtr.Zero);
        else if (p[0] == "D") mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
        else if (p[0] == "U") mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
        else if (p[0] == "EXIT") Exit = true;
    }

    static void Check(long now) {
        if (now - checkedAt < 250) return;
        checkedAt = now;
        apps = false;
        try {
            IntPtr h = GetForegroundWindow();
            uint pid; GetWindowThreadProcessId(h, out pid);
            using (Process p = Process.GetProcessById((int)pid)) {
                apps = TvMap.MediaApp(p.ProcessName);
            }
        } catch { apps = false; }
        if (now - steamAt > 2000) {
            steamAt = now;
            Process[] s = Process.GetProcessesByName("steam");
            steam = s.Length > 0;
            foreach (Process x in s) x.Dispose();
        }
    }

    static void Run() {
        Stopwatch clock = Stopwatch.StartNew();
        while (!Exit) {
            Thread.Sleep(16);
            ST s = new ST(); bool found = false;
            for (int i = 0; i < 4 && !found; i++) found = XInputGetState(i, out s) == 0;
            long now = clock.ElapsedMilliseconds;
            if (!found) { map.Step(0, 0, 0, 0, 0, 0, now, false); Thread.Sleep(250); continue; }
            Check(now);
            foreach (string a in map.Step(s.g.b, s.g.lx, s.g.ly, s.g.rx, s.g.ry, s.g.rt, now, apps && !steam)) Do(a);
        }
    }
}
'@
$ControleOk = $false
try {
  Add-Type -TypeDefinition $CodigoControle -ErrorAction Stop
  [TvPad]::Start()
  $ControleOk = $true
} catch { Log "controle de Xbox nos apps desligado: $_" }

$PedidoDaTela = $false   # "Sair do modo TV" nos ajustes da tela
function PedidoDeSair {
  if ($script:PedidoDaTela) { return $true }
  if ($ControleOk -and [TvPad]::Exit) { return $true }
  if ($Teste -and (Test-Path (Join-Path $Teste 'sair'))) { return $true }
  return $false
}

# ---------- O servidor da tela (so neste PC) ----------
$Tipos = @{ '.html' = 'text/html; charset=utf-8'; '.js' = 'application/javascript; charset=utf-8'; '.css' = 'text/css; charset=utf-8';
            '.png' = 'image/png'; '.svg' = 'image/svg+xml'; '.ttf' = 'font/ttf'; '.json' = 'application/json'; '.txt' = 'text/plain; charset=utf-8';
            '.jpg' = 'image/jpeg'; '.jpeg' = 'image/jpeg'; '.webp' = 'image/webp'; '.gif' = 'image/gif'; '.bmp' = 'image/bmp';
            '.mp4' = 'video/mp4'; '.webm' = 'video/webm' }
# A pasta Fundos, ao lado do INICIAR-TV.bat: imagens e videos para o plano de fundo da tela
$Fundos = Join-Path (Split-Path $Raiz) 'Fundos'
if ($Teste) { $Fundos = Join-Path $Teste 'Fundos' }
$ImagensFundo = @('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
$VideosFundo = @('.mp4', '.webm')
function ListaFundos {
  $img = @(); $vid = @()
  if (Test-Path -LiteralPath $Fundos) {
    foreach ($f in (Get-ChildItem -LiteralPath $Fundos -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
      $ext = $f.Extension.ToLowerInvariant()
      $url = '/fundos/' + [Uri]::EscapeDataString($f.Name)
      if ($ImagensFundo -contains $ext) { $img += $url } elseif ($VideosFundo -contains $ext) { $vid += $url }
    }
  }
  return @{ images = $img; videos = $vid }
}

# Abrir junto com o Windows: um atalho para o INICIAR-TV.bat na pasta Inicializar do usuario (so dele, sem admin)
function AtalhoInicio {
  $pasta = if ($Teste) { Join-Path $Teste 'Inicializar' } else { [Environment]::GetFolderPath('Startup') }
  return Join-Path $pasta 'Smart TV.lnk'
}
function InicioAutomatico($ligar) {
  $lnk = AtalhoInicio
  if ($null -ne $ligar) {
    if ($ligar) {
      $bat = Join-Path (Split-Path $Raiz) 'INICIAR-TV.bat'
      if ($Teste) { New-Item -ItemType Directory -Force -Path (Split-Path $lnk) | Out-Null; Set-Content -Path $lnk -Value $bat }
      else {
        $sh = New-Object -ComObject WScript.Shell
        $a = $sh.CreateShortcut($lnk)
        $a.TargetPath = $bat
        $a.WorkingDirectory = Split-Path $bat
        $a.WindowStyle = 7   # minimizado: so a tela de TV aparece
        $a.Save()
      }
      Log 'abrir junto com o Windows: ligado'
    } elseif (Test-Path -LiteralPath $lnk) {
      Remove-Item -LiteralPath $lnk -Force
      Log 'abrir junto com o Windows: desligado'
    }
  }
  return (Test-Path -LiteralPath $lnk)
}
$WebCheio = [System.IO.Path]::GetFullPath($Web).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

function Responder($fluxo, $codigo, $tipo, [byte[]]$corpo) {
  $cab = "HTTP/1.1 $codigo`r`nContent-Type: $tipo`r`nContent-Length: $($corpo.Length)`r`nCache-Control: no-store`r`nConnection: close`r`n`r`n"
  $b = [System.Text.Encoding]::ASCII.GetBytes($cab)
  $fluxo.Write($b, 0, $b.Length)
  if ($corpo.Length) { $fluxo.Write($corpo, 0, $corpo.Length) }
}
function Texto($fluxo, $codigo, $m) { Responder $fluxo $codigo 'text/plain; charset=utf-8' ([System.Text.Encoding]::UTF8.GetBytes($m)) }
function Json($fluxo, $obj) {
  Responder $fluxo '200 OK' 'application/json; charset=utf-8' ([System.Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json -Depth 5 -Compress)))
}

function Sobre {
  $sistema = 'Windows'; $ip = ''
  try { $so = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop; $sistema = "$($so.Caption) $($so.Version)" } catch {}
  try {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop | Where-Object { $_.IPAddress -notmatch '^(127|169\.254)\.' } |
           Select-Object -First 1).IPAddress
  } catch {}
  return @{ model = "$env:COMPUTERNAME"; firmware = ''; system = $sistema; version = 'PC 1.0'; ip = "$ip" }
}

# Um arquivo, em pedacos de ate 4 MB quando o navegador pede um trecho (videos): um video grande nunca segura a tela.
function ServirArquivo($fluxo, $arq, $intervalo) {
  $tipo = $Tipos[[System.IO.Path]::GetExtension($arq).ToLowerInvariant()]
  if (-not $tipo) { $tipo = 'application/octet-stream' }
  $fs = [System.IO.File]::Open($arq, 'Open', 'Read', 'ReadWrite')
  try {
    $total = $fs.Length
    $ini = 0; $fim = $total - 1; $codigo = '200 OK'; $extra = ''
    if ($intervalo -match '^bytes=(\d*)-(\d*)$') {
      if ($matches[1] -ne '') { $ini = [int64]$matches[1] }
      if ($matches[2] -ne '') { $fim = [Math]::Min([int64]$matches[2], $total - 1) }
      elseif ($matches[1] -eq '' -and $total -gt 0) { $ini = 0 }
      if ($ini -ge $total -and $total -gt 0) {
        $cab = "HTTP/1.1 416 Range Not Satisfiable`r`nContent-Range: bytes */$total`r`nContent-Length: 0`r`nConnection: close`r`n`r`n"
        $b = [System.Text.Encoding]::ASCII.GetBytes($cab); $fluxo.Write($b, 0, $b.Length); return
      }
      $fim = [Math]::Min($fim, $ini + 4MB - 1)
      $codigo = '206 Partial Content'; $extra = "Content-Range: bytes $ini-$fim/$total`r`n"
    }
    $tamanho = [Math]::Max(0, $fim - $ini + 1)
    $cab = "HTTP/1.1 $codigo`r`nContent-Type: $tipo`r`nContent-Length: $tamanho`r`nAccept-Ranges: bytes`r`n$extra" +
           "Cache-Control: no-store`r`nConnection: close`r`n`r`n"
    $b = [System.Text.Encoding]::ASCII.GetBytes($cab)
    $fluxo.Write($b, 0, $b.Length)
    [void]$fs.Seek($ini, 'Begin')
    $buf = New-Object byte[] 262144
    $falta = $tamanho
    while ($falta -gt 0) {
      $n = $fs.Read($buf, 0, [int][Math]::Min($buf.Length, $falta))
      if ($n -le 0) { break }
      $fluxo.Write($buf, 0, $n)
      $falta -= $n
    }
  } finally { $fs.Close() }
}

function Atender($cliente) {
  $fluxo = $cliente.GetStream()
  $fluxo.ReadTimeout = 2000
  $leitor = New-Object System.IO.StreamReader($fluxo, [System.Text.Encoding]::ASCII)
  $linha = $leitor.ReadLine()
  if (-not $linha -or $linha.Length -gt 4096) { return }
  # os cabecalhos: so o trecho pedido (Range) interessa
  $intervalo = ''
  for ($h = 0; $h -lt 60; $h++) {
    $c = $leitor.ReadLine()
    if ($null -eq $c -or $c -eq '') { break }
    if ($c -match '^Range:\s*(.+)$') { $intervalo = $matches[1].Trim() }
  }
  $partes = $linha.Split(' ')
  if ($partes.Length -lt 3 -or $partes[0] -ne 'GET' -or -not $partes[1].StartsWith('/')) { Texto $fluxo '400 Bad Request' 'pedido invalido'; return }
  $alvo = $partes[1]
  $q = $alvo.IndexOf('?')
  $caminhoBruto = if ($q -ge 0) { $alvo.Substring(0, $q) } else { $alvo }
  $consulta = if ($q -ge 0) { $alvo.Substring($q + 1) } else { '' }
  try { $caminho = [Uri]::UnescapeDataString($caminhoBruto) } catch { Texto $fluxo '400 Bad Request' 'pedido invalido'; return }
  # nada de caracteres de controle, barra invertida ou dois-pontos (no Windows, "arquivo:fluxo" abre partes escondidas)
  if ($caminho -match '[\x00-\x1f\x7f\\:]') { Texto $fluxo '400 Bad Request' 'pedido invalido'; return }
  $param = @{}
  foreach ($kv in $consulta.Split('&')) {
    if ($kv -match '^([^=]+)=(.*)$') { try { $param[$matches[1]] = [Uri]::UnescapeDataString($matches[2].Replace('+', ' ')) } catch {} }
  }

  switch ($caminho) {
    '/api/apps' {
      Json $fluxo @{ apps = @($Apps | ForEach-Object { @{ id = $_.id; title = $_.title; icon = $_.icon; color = $_.color } }) }
      return
    }
    '/api/open' { Json $fluxo @{ ok = [bool](AbrirApp $param['id']) }; return }
    '/api/settings' { Abrir 'ms-settings:' @(); Json $fluxo @{ ok = $true }; return }
    '/api/about' { Json $fluxo (Sobre); return }
    '/api/wallpapers' { Json $fluxo (ListaFundos); return }
    '/api/autostart' {
      $ligar = $null
      if ($param.ContainsKey('on')) { $ligar = ($param['on'] -eq '1') }
      $on = $false
      try { $on = InicioAutomatico $ligar } catch { Log "abrir junto com o Windows: $_" }
      Json $fluxo @{ on = [bool]$on }
      return
    }
    '/api/quit' { $script:PedidoDaTela = $true; Log 'sair pela tela'; Json $fluxo @{ ok = $true }; return }
  }
  if ($caminho.StartsWith('/fundos/')) {
    $nome = $caminho.Substring(8)
    $arqF = Join-Path $Fundos $nome
    if (-not $nome -or $nome.Contains('/') -or $nome.StartsWith('.') -or -not (Test-Path -LiteralPath $arqF -PathType Leaf) -or
        ($ImagensFundo + $VideosFundo) -notcontains [System.IO.Path]::GetExtension($nome).ToLowerInvariant()) {
      Texto $fluxo '404 Not Found' '404'; return
    }
    ServirArquivo $fluxo $arqF $intervalo
    return
  }
  if ($caminho -eq '/') { $caminho = '/index.html' }
  $relativo = $caminho.TrimStart('/').Replace('/', [string][System.IO.Path]::DirectorySeparatorChar)
  try { $arq = [System.IO.Path]::GetFullPath((Join-Path $Web $relativo)) } catch { Texto $fluxo '404 Not Found' '404'; return }
  if (-not $arq.StartsWith($WebCheio) -or -not (Test-Path -LiteralPath $arq -PathType Leaf)) { Texto $fluxo '404 Not Found' '404'; return }
  ServirArquivo $fluxo $arq ''
}

$ouvinte = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Porta)
try { $ouvinte.Start() } catch { Avisar "Outro programa esta usando a porta $Porta deste PC. Feche-o e abra o modo TV de novo."; exit 1 }
Log "ouvindo em $Base"

# ---------- A tela inicial em tela cheia ----------
Abrir $Navegador $ArgsTela

function TelaAberta {
  if ($Teste) { return -not (Test-Path (Join-Path $Teste 'tela-fechada')) }
  try {
    $p = Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" -ErrorAction Stop |
         Where-Object { $_.CommandLine -and $_.CommandLine.Contains("$Dados\home") }
    return [bool]$p
  } catch { return $true }   # sem como saber: segue aberto
}
function FecharTela {
  if ($Teste) { Log 'fecharia a tela'; return }
  try {
    Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" -ErrorAction Stop |
      Where-Object { $_.CommandLine -and $_.CommandLine.Contains("$Dados\home") } |
      ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName Terminate | Out-Null }
  } catch {}
}

# Um pedido so e lido quando o navegador manda algo: o Chromium abre conexoes "de reserva" que ficam mudas, e
# esperar por elas travaria a tela por segundos. As mudas por mais de 10 s sao fechadas.
$espera = New-Object System.Collections.ArrayList
$inicio = Get-Date
$conferido = Get-Date
$atendidos = 0
while (-not (PedidoDeSair)) {
  $fez = $false
  while ($ouvinte.Pending()) { [void]$espera.Add(@{ c = $ouvinte.AcceptTcpClient(); t = Get-Date }); $fez = $true }
  for ($i = $espera.Count - 1; $i -ge 0; $i--) {
    $e = $espera[$i]
    $pronto = $false
    try { $pronto = $e.c.Available -gt 0 } catch {}
    if ($pronto) {
      $espera.RemoveAt($i)
      try { Atender $e.c; $atendidos++ } catch { Log "pedido: $_" } finally { $e.c.Close() }
      $fez = $true
    } elseif (((Get-Date) - $e.t).TotalSeconds -gt 10) {
      $espera.RemoveAt($i)
      try { $e.c.Close() } catch {}
    }
  }
  if (-not $fez) { Start-Sleep -Milliseconds 15 }
  # a tela inicial foi fechada (Alt+F4): o modo TV termina
  if (((Get-Date) - $conferido).TotalSeconds -gt 3 -and ((Get-Date) - $inicio).TotalSeconds -gt 15) {
    $conferido = Get-Date
    if (-not (TelaAberta)) { Log 'tela fechada'; break }
  }
}
if ($ControleOk) { [TvPad]::Exit = $true }
FecharTela
foreach ($e in $espera) { try { $e.c.Close() } catch {} }
$ouvinte.Stop()
Log "fim ($atendidos pedidos)"
