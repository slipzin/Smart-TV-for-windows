"""Runs the real tv.ps1 in test mode (-Teste) against a pretend PC and checks the server and the app list.

    python3 -I pc/test/servidor.py <built package>   (pc/test.sh runs it)

The pretend PC: Start menu apps (Store apps, a program and a website shortcut that must be left out), a Steam with
Call of Duty in a second library, no Edge (test mode). Nothing on this computer is opened.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

PACOTE = os.path.abspath(sys.argv[1])
PWSH = os.environ.get('PWSH', 'pwsh')
PORTA = 48765
falhas = []


def confere(nome, ok, detalhe=''):
    print(('ok: ' if ok else 'FALHOU: ') + nome + ('' if ok else '  ' + str(detalhe)))
    if not ok:
        falhas.append(nome)


def get(caminho, timeout=5):
    with urllib.request.urlopen('http://127.0.0.1:%d%s' % (PORTA, caminho), timeout=timeout) as r:
        return r.status, r.headers.get('Content-Type'), r.read()


def bruto(dados, timeout=5):
    s = socket.create_connection(('127.0.0.1', PORTA), timeout=timeout)
    s.sendall(dados)
    out = b''
    try:
        while True:
            b = s.recv(65536)
            if not b:
                break
            out += b
    except socket.timeout:
        out += b'<timeout>'
    s.close()
    return out


def pc_falso(d):
    apps = [
        {'Name': 'Netflix', 'AppID': '4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App'},
        {'Name': 'Prime Video for Windows', 'AppID': 'AmazonVideo.PrimeVideo_pwbj9vvecjh7j!App'},
        {'Name': 'Disney+', 'AppID': 'Disney.37853FC22B2CE_6rarf9sa4v8jt!App'},
        {'Name': 'Spotify', 'AppID': 'SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify'},
        {'Name': 'Xbox', 'AppID': 'Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App'},
        {'Name': 'Battle.net', 'AppID': '{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}\\Battle.net\\Battle.net Launcher.exe'},
        # a website "installed as an app" by Edge: must not show
        {'Name': 'YouTube', 'AppID': 'MSEdge._crx_agimnkijcaahngcdmfeangaknmldooml'},
        {'Name': 'Globoplay', 'AppID': 'https://globoplay.globo.com/'},
        {'Name': 'Calculadora', 'AppID': 'Microsoft.WindowsCalculator_8wekyb3d8bbwe!App'},
    ]
    with open(os.path.join(d, 'startapps.json'), 'w', encoding='utf-8') as f:
        json.dump(apps, f)
    steam = os.path.join(d, 'Steam')
    lib2 = os.path.join(d, 'Jogos', 'SteamLibrary')
    os.makedirs(os.path.join(steam, 'steamapps'))
    os.makedirs(os.path.join(lib2, 'steamapps'))
    open(os.path.join(steam, 'steam.exe'), 'w').close()
    with open(os.path.join(steam, 'steamapps', 'libraryfolders.vdf'), 'w') as f:
        f.write('"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n\t"1"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n'
                % (steam.replace('\\', '\\\\'), lib2.replace('\\', '\\\\')))
    open(os.path.join(lib2, 'steamapps', 'appmanifest_1938090.acf'), 'w').close()
    with open(os.path.join(d, 'steam.txt'), 'w') as f:
        f.write(os.path.join(steam, 'steam.exe'))
    # the Fundos folder: two pictures, a 10 MB video, and files that must not show
    fundos = os.path.join(d, 'Fundos')
    os.makedirs(fundos)
    png = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                        '1f15c4890000000d49444154789c6360f80f0000010101005d0b8d6a0000000049454e44ae426082')
    for n in ('b paisagem.jpg', 'a.png'):
        with open(os.path.join(fundos, n), 'wb') as f:
            f.write(png)
    with open(os.path.join(fundos, 'video.mp4'), 'wb') as f:
        f.write(os.urandom(10 * 1024 * 1024))
    for n in ('LEIA-ME.txt', '.escondido.png', 'programa.exe'):
        open(os.path.join(fundos, n), 'w').close()


def main():
    d = tempfile.mkdtemp(prefix='stv-pc-')
    pc_falso(d)
    proc = subprocess.Popen([PWSH, '-NoProfile', '-File', os.path.join(PACOTE, 'sistema', 'tv.ps1'), '-Teste', d],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                socket.create_connection(('127.0.0.1', PORTA), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.2)
        else:
            confere('o servidor comecou', False, proc.stdout.read().decode(errors='replace'))
            return

        # the home screen was opened in kiosk mode
        abertos = open(os.path.join(d, 'abertos.txt'), encoding='utf-8').read()
        confere('abriu a tela em modo quiosque', '--kiosk' in abertos and 'http://127.0.0.1:48765/' in abertos, abertos)

        # the app list: Store apps, Steam and its Call of Duty; never a website shortcut nor the calculator
        st, tipo, corpo = get('/api/apps')
        apps = json.loads(corpo)['apps']
        ids = [a['id'] for a in apps]
        confere('lista de apps em JSON', st == 200 and tipo.startswith('application/json'), tipo)
        confere('apps instalados aparecem', ids == ['netflix', 'amazon', 'disney', 'spotify', 'xbox', 'battlenet', 'steam', 'cod'], ids)
        confere('atalho de site do Edge (YouTube) fica de fora', 'youtube.leanback.v4' not in ids)
        confere('endereco da web (Globoplay) fica de fora', 'globoplay' not in ids)
        confere('cada app tem nome e cor', all(a['title'] and a['color'] for a in apps), apps)

        # opening each one: by the Start menu (shell:AppsFolder), Steam by its links; never the browser
        for i in ids:
            st, _, corpo = get('/api/open?id=' + i)
            confere('abre ' + i, json.loads(corpo) == {'ok': True}, corpo)
        abertos = open(os.path.join(d, 'abertos.txt'), encoding='utf-8').read().splitlines()[1:]
        esperado = ['shell:AppsFolder\\4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App',
                    'shell:AppsFolder\\AmazonVideo.PrimeVideo_pwbj9vvecjh7j!App',
                    'shell:AppsFolder\\Disney.37853FC22B2CE_6rarf9sa4v8jt!App',
                    'shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify',
                    'shell:AppsFolder\\Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App',
                    'shell:AppsFolder\\{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}\\Battle.net\\Battle.net Launcher.exe',
                    'steam://open/bigpicture', 'steam://rungameid/1938090']
        confere('cada app abriu pelo caminho certo', [a.split(' | ')[0] for a in abertos] == esperado, abertos)
        confere('nenhum app abriu pelo navegador', not any(a.startswith('navegador') for a in abertos), abertos)
        st, _, corpo = get('/api/open?id=naoexiste')
        confere('app que nao existe: ok=false', json.loads(corpo) == {'ok': False}, corpo)
        st, _, corpo = get('/api/open?id=')
        confere('sem id: ok=false', json.loads(corpo) == {'ok': False}, corpo)
        st, _, corpo = get('/api/settings')
        confere('ajustes do Windows', json.loads(corpo) == {'ok': True} and 'ms-settings:' in open(os.path.join(d, 'abertos.txt')).read())
        st, _, corpo = get('/api/about')
        sobre = json.loads(corpo)
        confere('sobre este PC', set(sobre) >= {'model', 'system', 'version', 'ip'}, sobre)

        # the Fundos folder: pictures and videos only, in name order, as addresses the page can load
        st, _, corpo = get('/api/wallpapers')
        f = json.loads(corpo)
        confere('lista os fundos', f == {'images': ['/fundos/a.png', '/fundos/b%20paisagem.jpg'], 'videos': ['/fundos/video.mp4']}, f)
        st, tipo, corpo = get('/fundos/b%20paisagem.jpg')
        confere('serve uma imagem de fundo', st == 200 and tipo == 'image/jpeg' and corpo.startswith(b'\x89PNG'), (st, tipo))
        tamanho = 10 * 1024 * 1024
        r = bruto(b'GET /fundos/video.mp4 HTTP/1.1\r\nRange: bytes=0-\r\n\r\n', timeout=10)
        cab, _, corpo = r.partition(b'\r\n\r\n')
        confere('video em pedacos de 4 MB (206)', cab.startswith(b'HTTP/1.1 206') and b'Content-Range: bytes 0-4194303/%d' % tamanho in cab
                and len(corpo) == 4 * 1024 * 1024, cab[:200])
        r = bruto(b'GET /fundos/video.mp4 HTTP/1.1\r\nRange: bytes=9437184-\r\n\r\n', timeout=10)
        cab, _, corpo = r.partition(b'\r\n\r\n')
        confere('o fim do video', b'Content-Range: bytes 9437184-%d/%d' % (tamanho - 1, tamanho) in cab and len(corpo) == tamanho - 9437184, cab[:200])
        with open(os.path.join(d, 'Fundos', 'video.mp4'), 'rb') as v:
            v.seek(5000000)
            trecho = v.read(1000)
        r = bruto(b'GET /fundos/video.mp4 HTTP/1.1\r\nRange: bytes=5000000-5000999\r\n\r\n', timeout=10)
        confere('o trecho certo do video', r.partition(b'\r\n\r\n')[2] == trecho)
        confere('trecho fora do video: 416', bruto(b'GET /fundos/video.mp4 HTTP/1.1\r\nRange: bytes=99999999-\r\n\r\n').startswith(b'HTTP/1.1 416'))
        for errado in ['/fundos/LEIA-ME.txt', '/fundos/.escondido.png', '/fundos/programa.exe', '/fundos/..', '/fundos/', '/fundos/nao.png']:
            r = bruto(b'GET ' + errado.encode() + b' HTTP/1.1\r\n\r\n')
            confere('recusa ' + errado, r.startswith(b'HTTP/1.1 404') or r.startswith(b'HTTP/1.1 400'), r[:40])
        # opening with Windows: a shortcut in the user's Startup folder, and gone again
        confere('abrir com o Windows: desligado no inicio', json.loads(get('/api/autostart')[2]) == {'on': False})
        confere('abrir com o Windows: liga', json.loads(get('/api/autostart?on=1')[2]) == {'on': True}
                and os.path.exists(os.path.join(d, 'Inicializar', 'Smart TV.lnk')))
        confere('abrir com o Windows: continua ligado', json.loads(get('/api/autostart')[2]) == {'on': True})
        confere('abrir com o Windows: desliga', json.loads(get('/api/autostart?on=0')[2]) == {'on': False}
                and not os.path.exists(os.path.join(d, 'Inicializar', 'Smart TV.lnk')))

        # files: the page and its parts, with the right types
        for caminho, tipo_esperado in [('/', 'text/html'), ('/tv.js', 'application/javascript'), ('/home.css', 'text/css'),
                                       ('/icons/netflix.svg', 'image/svg+xml'), ('/symbols/gamepad.png', 'image/png'),
                                       ('/fonts/InterVariable.ttf', 'font/ttf'), ('/i18n.js', 'application/javascript')]:
            st, tipo, corpo = get(caminho)
            confere('serve ' + caminho, st == 200 and tipo.startswith(tipo_esperado) and len(corpo) > 0, (st, tipo))
        # nothing outside the page's folder, nothing odd
        for ataque in [b'GET /../../../../etc/passwd HTTP/1.1\r\n\r\n', b'GET /%2e%2e/%2e%2e/etc/passwd HTTP/1.1\r\n\r\n',
                       b'GET /..%5c..%5c..%5cwindows%5cwin.ini HTTP/1.1\r\n\r\n', b'GET /sistema/../tv.ps1 HTTP/1.1\r\n\r\n',
                       b'GET //etc/passwd HTTP/1.1\r\n\r\n', b'GET /%00 HTTP/1.1\r\n\r\n',
                       b'GET /index.html:secreto HTTP/1.1\r\n\r\n', b'GET /C:/Windows/win.ini HTTP/1.1\r\n\r\n',
                       b'GET /%5cWindows%5cwin.ini HTTP/1.1\r\n\r\n']:
            r = bruto(ataque)
            confere('recusa ' + ataque.split(b' ')[1].decode(), r.startswith(b'HTTP/1.1 404') or r.startswith(b'HTTP/1.1 400'), r[:60])
        confere('recusa POST', bruto(b'POST /api/open?id=netflix HTTP/1.1\r\nContent-Length: 0\r\n\r\n').startswith(b'HTTP/1.1 400'))
        confere('recusa pedido sem sentido', bruto(b'lixo\r\n\r\n').startswith(b'HTTP/1.1 400'))
        r = bruto(b'GET /' + b'a' * 10000 + b' HTTP/1.1\r\n\r\n')
        confere('pedido gigante nao derruba', b'<timeout>' not in r, r[:60])

        # the browser's silent "spare" connections must not hold the page up
        mudas = [socket.create_connection(('127.0.0.1', PORTA)) for _ in range(6)]
        t0 = time.time()
        st, _, _ = get('/home.js')
        demora = time.time() - t0
        confere('conexoes mudas nao atrasam a tela (%.2f s)' % demora, st == 200 and demora < 1.0, demora)
        for m in mudas:
            m.close()

        # many at once, like the page loading all its icons
        erros = []

        def um(i):
            try:
                st, _, corpo = get(['/', '/tv.js', '/home.js', '/api/apps', '/icons/prime.png'][i % 5], timeout=15)
                if st != 200 or not corpo:
                    erros.append(i)
            except Exception as e:  # noqa: BLE001
                erros.append((i, str(e)))
        t0 = time.time()
        fios = [threading.Thread(target=um, args=(i,)) for i in range(200)]
        for f in fios:
            f.start()
        for f in fios:
            f.join()
        confere('200 pedidos ao mesmo tempo, sem erro (%.1f s)' % (time.time() - t0), not erros, erros[:5])

        # still alive after all that
        st, _, _ = get('/api/apps')
        confere('servidor continua de pe', st == 200)

        # a second start only brings the home screen back (no second server)
        r2 = subprocess.run([PWSH, '-NoProfile', '-File', os.path.join(PACOTE, 'sistema', 'tv.ps1'), '-Teste', d],
                            capture_output=True, timeout=60)
        log = open(os.path.join(d, 'tv.log'), encoding='utf-8').read()
        confere('abrir de novo so traz a tela de volta', r2.returncode == 0 and 'ja estava aberto' in log, log[-300:])

        # leaving: Settings > Leave TV mode ends it
        confere('sair pela tela responde', json.loads(get('/api/quit')[2]) == {'ok': True})
        try:
            proc.wait(timeout=30)
            confere('sair pela tela encerra o modo TV', proc.returncode == 0)
        except subprocess.TimeoutExpired:
            confere('sair pela tela encerra o modo TV', False, 'nao terminou em 30 s')
        log = open(os.path.join(d, 'tv.log'), encoding='utf-8').read()
        confere('registro sem erros', 'erro' not in log.lower() and 'pedido:' not in log, log)
        try:
            socket.create_connection(('127.0.0.1', PORTA), timeout=0.5).close()
            confere('porta liberada no fim', False)
        except OSError:
            confere('porta liberada no fim', True)
    finally:
        if proc.poll() is None:
            proc.kill()
        shutil.rmtree(d, ignore_errors=True)
    print('%d falha(s)' % len(falhas) if falhas else 'servidor: todos os testes passaram')
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
