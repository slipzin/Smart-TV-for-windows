// The home screen in a real browser, served by the real tv.ps1 in test mode, driven by a pretend game controller.
//   node pc/test/tela.js <built package> <out dir> [minutes of stress, default 3]   (pc/test.sh runs it)
// Checks: every screen size fits, the controller and the keyboard move and open, the top buttons, no script errors,
// and a long run of random presses without errors, leaks or a stuck page.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');

const PACOTE = path.resolve(process.argv[2]);
const OUT = path.resolve(process.argv[3] || '.');
const MINUTOS = parseFloat(process.argv[4] || '3');
const PWSH = process.env.PWSH || 'pwsh';
let falhas = 0;
function confere(nome, ok, detalhe) {
  console.log((ok ? 'ok: ' : 'FALHOU: ') + nome + (ok || detalhe === undefined ? '' : '  ' + JSON.stringify(detalhe)));
  if (!ok) falhas++;
}
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
function porta() {
  return new Promise((r) => { const s = net.connect(48765, '127.0.0.1', () => { s.end(); r(true); }); s.on('error', () => r(false)); });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'stv-tela-'));
  fs.writeFileSync(path.join(d, 'startapps.json'), JSON.stringify([
    { Name: 'Netflix', AppID: '4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App' },
    { Name: 'Prime Video for Windows', AppID: 'AmazonVideo.PrimeVideo_pwbj9vvecjh7j!App' },
    { Name: 'Disney+', AppID: 'Disney.37853FC22B2CE_6rarf9sa4v8jt!App' },
    { Name: 'Apple TV', AppID: 'AppleInc.AppleTV_nzyj5cx40ttqa!App' },
    { Name: 'Spotify', AppID: 'SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify' },
    { Name: 'Xbox', AppID: 'Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App' },
  ]));
  const steam = path.join(d, 'Steam');
  fs.mkdirSync(path.join(steam, 'steamapps'), { recursive: true });
  fs.writeFileSync(path.join(steam, 'steam.exe'), '');
  fs.writeFileSync(path.join(d, 'steam.txt'), path.join(steam, 'steam.exe'));
  const srv = spawn(PWSH, ['-NoProfile', '-File', path.join(PACOTE, 'sistema', 'tv.ps1'), '-Teste', d], { stdio: 'ignore' });
  for (let i = 0; i < 100 && !(await porta()); i++) await espera(200);
  const abertos = () => (fs.existsSync(path.join(d, 'abertos.txt')) ? fs.readFileSync(path.join(d, 'abertos.txt'), 'utf8') : '');

  const browser = await chromium.launch();
  const erros = [];
  async function pagina(w, h, extra) {
    const p = await browser.newPage({ viewport: { width: w, height: h }, locale: 'pt-BR' });
    p.on('pageerror', (e) => erros.push(e.message));
    await p.addInitScript(() => {
      window.__pad = { buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })), axes: [0, 0, 0, 0] };
      navigator.getGamepads = () => [Object.assign({ id: 'Wireless Controller', index: 0, mapping: 'standard', connected: true }, window.__pad)];
    });
    if (extra) await p.addInitScript(extra);
    await p.goto('http://127.0.0.1:48765/', { waitUntil: 'networkidle' });
    await p.waitForTimeout(2500);
    return p;
  }
  const B = { A: 0, B: 1, UP: 12, DOWN: 13, LEFT: 14, RIGHT: 15 };
  async function aperta(p, botao, ms) {
    await p.evaluate((i) => { window.__pad.buttons[i].pressed = true; }, botao);
    await p.waitForTimeout(ms || 120);
    await p.evaluate((i) => { window.__pad.buttons[i].pressed = false; }, botao);
    await p.waitForTimeout(300);
  }
  const foco = (p) => p.evaluate(() => {
    const f = document.querySelector('.focus');
    return f ? (f.getAttribute('aria-label') || f.textContent || f.className).trim().slice(0, 40) : null;
  });

  // 1. Every common PC screen: the stage fits inside the window, without scroll bars
  for (const [w, h] of [[1920, 1080], [1366, 768], [1280, 720], [2560, 1440], [3840, 2160], [1920, 1200], [3440, 1440], [1600, 900]]) {
    const p = await pagina(w, h);
    const r = await p.evaluate(() => {
      const s = document.getElementById('stage').getBoundingClientRect();
      return { l: s.left, t: s.top, r: s.right, b: s.bottom, sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight,
               vw: innerWidth, vh: innerHeight, tiles: document.querySelectorAll('#shelf .tile, #shelf button, .tile').length };
    });
    const cabe = r.l >= -1 && r.t >= -1 && r.r <= r.vw + 1 && r.b <= r.vh + 1 && r.sw <= r.vw + 1 && r.sh <= r.vh + 1;
    confere(`tela ${w}x${h} cabe sem rolagem`, cabe, r);
    const centro = Math.abs((r.l + r.r) / 2 - r.vw / 2) <= 2 && Math.abs((r.t + r.b) / 2 - r.vh / 2) <= 2;
    confere(`tela ${w}x${h} centralizada`, centro, r);
    await p.screenshot({ path: path.join(OUT, `tela-${w}x${h}.png`) });
    await p.close();
  }

  // 2. The controller: along the shelf, open an app with A, the top buttons
  let p = await pagina(1920, 1080);
  const inicio = await foco(p);
  await aperta(p, B.RIGHT); await aperta(p, B.RIGHT);
  const depois = await foco(p);
  confere('D-pad move o foco na prateleira', inicio !== depois, [inicio, depois]);
  await aperta(p, B.LEFT); await aperta(p, B.LEFT);
  confere('volta ao primeiro app', (await foco(p)) === inicio, [inicio, await foco(p)]);
  const antes = abertos().split('\n').length;
  await aperta(p, B.A);
  await p.waitForTimeout(800);
  const novos = abertos().split('\n').slice(antes - 1).join(' ');
  confere('A abre o app pelo menu Iniciar (Netflix)', /shell:AppsFolder\\4DF9E0F8\.Netflix/.test(novos), novos);
  // held right: it repeats, several apps in one hold
  const f0 = await p.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.tile'), document.querySelector('.tile.focus')));
  await aperta(p, B.RIGHT, 1100);
  const f1 = await p.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.tile'), document.querySelector('.tile.focus')));
  confere('segurar a seta repete (andou ' + (f1 - f0) + ')', f1 - f0 >= 3, [f0, f1]);
  // the left stick too
  await p.evaluate(() => { window.__pad.axes[0] = -1; });
  await p.waitForTimeout(150);
  await p.evaluate(() => { window.__pad.axes[0] = 0; });
  await p.waitForTimeout(300);
  const f2 = await p.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.tile'), document.querySelector('.tile.focus')));
  confere('analogico esquerdo move', f2 === f1 - 1, [f1, f2]);
  // up to the top buttons: Games opens Steam's Big Picture
  for (let i = 0; i < 4; i++) await aperta(p, B.UP);
  const topo = await p.evaluate(() => { const f = document.querySelector('#buttons .focus'); return f ? f.textContent : null; });
  confere('botao Jogos no topo', topo && /Jogos/.test(topo), topo);
  await aperta(p, B.A);
  await p.waitForTimeout(800);
  confere('Jogos abre o Big Picture da Steam', abertos().includes('steam://open/bigpicture'), abertos().slice(-200));
  await p.screenshot({ path: path.join(OUT, 'topo-jogos.png') });
  // B goes back down to the shelf
  await aperta(p, B.B);
  await p.waitForTimeout(400);
  const naPrateleira = await p.evaluate(() => !!document.querySelector('.tile.focus'));
  confere('B volta para a prateleira', naPrateleira);
  // the keyboard works the same
  const k0 = await p.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.tile'), document.querySelector('.tile.focus')));
  await p.keyboard.press('ArrowRight');
  await p.waitForTimeout(300);
  const k1 = await p.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.tile'), document.querySelector('.tile.focus')));
  confere('teclado: seta move', k1 === k0 + 1 || (k0 === k1 && k0 > 0), [k0, k1]);
  await p.close();

  // 3. Customizing: Settings from the gear, every background, the animation stops behind an app
  fs.mkdirSync(path.join(d, 'Fundos'), { recursive: true });
  fs.copyFileSync(path.join(OUT, 'tela-1920x1080.png'), path.join(d, 'Fundos', 'minha foto.png'));
  fs.copyFileSync(path.join(OUT, 'tela-1366x768.png'), path.join(d, 'Fundos', 'outra foto.png'));
  p = await pagina(1920, 1080);
  for (let i = 0; i < 4; i++) await aperta(p, B.UP);
  await aperta(p, B.RIGHT); await aperta(p, B.RIGHT);
  await aperta(p, B.A);
  await p.waitForTimeout(600);
  const linhas = await p.evaluate(() => Array.prototype.map.call(document.querySelectorAll('#settings .row'), (r) => r.textContent));
  confere('ajustes abrem pela engrenagem com Plano de fundo primeiro', linhas.length > 5 && /Plano de fundo/.test(linhas[0]), linhas.slice(0, 3));
  confere('ajustes tem Abrir junto com o Windows e Sair do modo TV',
    linhas.some((l) => /Abrir junto com o Windows/.test(l)) && linhas.some((l) => /Sair do modo TV/.test(l)), linhas);
  const vistos = [];
  for (let i = 0; i < 14; i++) {
    const info = await p.evaluate(() => ({
      nome: document.querySelector('#settings .row').textContent,
      chave: Wall.key(), ligado: document.body.className.indexOf('wall-on') >= 0,
      noite: document.body.className.indexOf('night') >= 0, anima: Wall.running(),
      visivel: !!document.getElementById('wall') && getComputedStyle(document.getElementById('wall')).display !== 'none'
    }));
    if (vistos.indexOf(info.chave) >= 0) break;
    vistos.push(info.chave);
    const animado = ['aurora', 'waves', 'stars', 'fluid', 'bubbles'].indexOf(info.chave) >= 0;
    if (info.chave === 'default') confere('fundo padrao: o das capas', !info.ligado && !info.visivel, info);
    else confere('fundo ' + info.chave + ' aparece' + (animado ? ' e anima' : ''), info.ligado && info.visivel && (!animado || info.anima), info);
    if (['lavender', 'sand'].indexOf(info.chave) >= 0) confere('fundo claro ' + info.chave + ': texto escuro', !info.noite, info);
    else if (info.chave !== 'default') confere('fundo escuro ' + info.chave + ': texto claro', info.noite, info);
    await p.evaluate(() => { var s = document.getElementById('settings'); s.style.visibility = 'hidden'; });
    await p.waitForTimeout(animado ? 700 : 1800);
    await p.screenshot({ path: path.join(OUT, 'fundo-' + info.chave + '.png') });
    await p.evaluate(() => { document.getElementById('settings').style.visibility = ''; });
    await aperta(p, B.RIGHT);
  }
  confere('todos os planos de fundo passaram (' + vistos.length + ')', vistos.length === 13, vistos);
  // an animated one, then the screen goes behind an app: the animation stops, and starts again when it is back
  while ((await p.evaluate(() => Wall.key())) !== 'aurora') await aperta(p, B.RIGHT);
  confere('aurora animando', await p.evaluate(() => Wall.running()));
  await p.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); });
  await p.waitForTimeout(300);
  confere('animacao para com um app na frente', !(await p.evaluate(() => Wall.running())));
  await p.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => false }); document.dispatchEvent(new Event('visibilitychange')); });
  await p.waitForTimeout(300);
  confere('animacao volta com a tela', await p.evaluate(() => Wall.running()));
  // the other rows: speed, darken, blur change the look
  await aperta(p, B.DOWN); await aperta(p, B.RIGHT);
  confere('velocidade muda', await p.evaluate(() => Prefs.get('wallSpeed') === 'fast'));
  await aperta(p, B.DOWN); await aperta(p, B.RIGHT);
  const escuro = await p.evaluate(() => getComputedStyle(document.querySelector('#wall .shade')).backgroundColor);
  confere('escurecer muda (' + escuro + ')', /0\.5\)$/.test(escuro), escuro);
  await aperta(p, B.DOWN); await aperta(p, B.RIGHT);
  const filtro = await p.evaluate(() => document.querySelector('#wall canvas').style.filter);
  confere('desfocar muda (' + filtro + ')', /blur\(8px\)/.test(filtro), filtro);
  // the choice stays after a new start (saved in this PC's profile)
  await p.reload({ waitUntil: 'networkidle' });
  await p.waitForTimeout(2000);
  confere('o fundo escolhido continua depois de abrir de novo', await p.evaluate(() => Wall.key() === 'aurora' && Wall.running()));
  await p.close();

  // 4. Night look, as the screen keeps it at night
  p = await pagina(1920, 1080, () => { try { localStorage.setItem('stv.night', 'true'); } catch (e) {} });
  await p.screenshot({ path: path.join(OUT, 'tela-noite.png') });
  await p.close();

  // 5. A long run: random presses for minutes, like a person zapping around; no errors, no leak, still answering
  p = await pagina(1920, 1080, () => { try { localStorage.setItem('stv.prefs', JSON.stringify({ wall: 'aurora' })); } catch (e) {} });
  const cdp = await p.context().newCDPSession(p);
  await cdp.send('Performance.enable');
  async function memoria() {
    await cdp.send('HeapProfiler.collectGarbage');
    const m = await cdp.send('Performance.getMetrics');
    const v = (n) => (m.metrics.find((x) => x.name === n) || {}).value;
    return { heap: v('JSHeapUsedSize'), nos: v('Nodes'), ouvintes: v('JSEventListeners') };
  }
  const m0 = await memoria();
  const fim = Date.now() + MINUTOS * 60000;
  let apertos = 0;
  const pesos = [B.RIGHT, B.RIGHT, B.LEFT, B.LEFT, B.UP, B.DOWN, B.DOWN, B.B];   // no A: opening apps is checked above
  while (Date.now() < fim) {
    await aperta(p, pesos[Math.floor(Math.random() * pesos.length)], 60 + Math.floor(Math.random() * 200));
    apertos++;
  }
  // back to a known place, and it still answers
  for (let i = 0; i < 6; i++) await aperta(p, B.DOWN);
  const m1 = await memoria();
  const vivo = await p.evaluate(() => document.querySelectorAll('.tile').length);
  confere(`resistencia: ${apertos} apertos em ${MINUTOS} min, tela ainda responde`, vivo > 0, vivo);
  confere('resistencia: memoria estavel (' + Math.round(m0.heap / 1e6) + ' -> ' + Math.round(m1.heap / 1e6) + ' MB)',
    m1.heap < m0.heap * 1.6 + 5e6, [m0, m1]);
  confere('resistencia: elementos da pagina estaveis (' + m0.nos + ' -> ' + m1.nos + ')', m1.nos < m0.nos * 1.5 + 500, [m0, m1]);
  confere('resistencia: ouvintes estaveis (' + m0.ouvintes + ' -> ' + m1.ouvintes + ')', m1.ouvintes < m0.ouvintes * 1.5 + 200, [m0, m1]);
  await p.screenshot({ path: path.join(OUT, 'depois-da-resistencia.png') });
  await p.close();

  confere('nenhum erro de script na tela', erros.length === 0, erros.slice(0, 5));
  await browser.close();
  fs.writeFileSync(path.join(d, 'sair'), '');
  await espera(1500);
  srv.kill();
  fs.rmSync(d, { recursive: true, force: true });
  console.log(falhas ? falhas + ' falha(s)' : 'tela: todos os testes passaram');
  process.exit(falhas ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
