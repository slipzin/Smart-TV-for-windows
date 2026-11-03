/*
 * Backgrounds for the home screen (Settings > Background): animated ones drawn here on a small canvas and stretched
 * over the screen (soft by nature, and cheap: about 1% of a GPU), still ones (gradients), and the person's own
 * pictures and videos from the Fundos folder beside INICIAR-TV.bat (an animated GIF moves by itself; several
 * pictures take turns). Only on the PC (tv.ps1 lists the folder). The animation stops whenever the screen is
 * hidden (an app or a game in front), so it never takes anything from them.
 * Plain ES5, as the rest of web/.
 */
var Wall = (function () {
  'use strict';

  // key, English name (translated by tr), kind, dark (white text over it), colors
  var CHOICES = [
    ['default', 'From the picks', 'default', null],
    ['aurora', 'Aurora', 'anim', true],
    ['waves', 'Waves', 'anim', true],
    ['stars', 'Starry sky', 'anim', true],
    ['fluid', 'Fluid colors', 'anim', true],
    ['bubbles', 'Bubbles', 'anim', true],
    ['ocean', 'Ocean', 'still', true, ['#0B3D91', '#062456', '#021029']],
    ['sunset', 'Sunset', 'still', true, ['#FF7A59', '#C2366B', '#3A1C5C']],
    ['forest', 'Forest', 'still', true, ['#2F6B3B', '#163D25', '#08180F']],
    ['graphite', 'Graphite', 'still', true, ['#3A3A3E', '#1F1F22', '#0B0B0D']],
    ['lavender', 'Lavender', 'still', false, ['#F4EEFF', '#E2D6FA', '#CBB8F2']],
    ['sand', 'Sand', 'still', false, ['#FBF6EE', '#F1E4CF', '#E2CDA9']],
    ['mine', 'My pictures', 'mine', true],
    ['video', 'My videos', 'video', true]
  ];
  var SPEEDS = {slow: 0.5, normal: 1, fast: 2};

  var box, canvas, ctx, video, imgs = [], shade, raf = 0, last = 0, t = 0;
  var mine = {images: [], videos: []}, slide = 0, slideTimer = 0, current = null;

  function byKey(key) {
    for (var i = 0; i < CHOICES.length; i++) if (CHOICES[i][0] === key) return CHOICES[i];
    return CHOICES[0];
  }

  /** The choices the PC can show now: My pictures / My videos only when the Fundos folder has some. */
  function choices() {
    var out = [];
    for (var i = 0; i < CHOICES.length; i++) {
      var c = CHOICES[i];
      if (c[2] === 'mine' && !mine.images.length) continue;
      if (c[2] === 'video' && !mine.videos.length) continue;
      out.push(c[0]);
    }
    return out;
  }

  function pref(name, fallback) { var v = Prefs.get(name); return v === undefined || v === null ? fallback : v; }
  function key() { var k = pref('wall', 'default'); return choices().indexOf(k) >= 0 ? k : 'default'; }

  function make() {
    if (box) return;
    var sky = document.getElementById('sky');
    box = document.createElement('div');
    box.id = 'wall';
    imgs = [document.createElement('div'), document.createElement('div')];
    for (var i = 0; i < 2; i++) { imgs[i].className = 'pic'; box.appendChild(imgs[i]); }
    video = document.createElement('video');
    video.muted = true; video.loop = true; video.setAttribute('playsinline', ''); video.setAttribute('muted', '');
    box.appendChild(video);
    canvas = document.createElement('canvas');
    canvas.width = 480; canvas.height = 270;
    ctx = canvas.getContext('2d');
    box.appendChild(canvas);
    shade = document.createElement('div');
    shade.className = 'shade';
    box.appendChild(shade);
    sky.insertBefore(box, sky.querySelector('.veil'));   // under the veil and the drawer's lift
    document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); else if (current && current[2] === 'anim') run(); });
  }

  // MARK: - The animated ones (480 x 270, stretched; t in seconds, already scaled by the speed)

  var stars = null, bubbles = null;
  function seeded(n, f) { var out = [], s = 7; for (var i = 0; i < n; i++) { s = (s * 9301 + 49297) % 233280; out.push(f(s / 233280, i)); } return out; }

  var DRAW = {
    aurora: function (c, t) {
      c.globalCompositeOperation = 'source-over';
      c.fillStyle = '#05060F'; c.fillRect(0, 0, 480, 270);
      c.globalCompositeOperation = 'lighter';
      var blobs = [[0.13, 0.07, '40,220,170'], [0.09, 0.11, '70,110,255'], [0.07, 0.05, '170,70,255'], [0.11, 0.13, '20,160,230']];
      for (var i = 0; i < blobs.length; i++) {
        var b = blobs[i], x = 240 + Math.sin(t * b[0] + i * 1.7) * 200, y = 110 + Math.cos(t * b[1] + i) * 70, r = 180 + Math.sin(t * 0.2 + i) * 40;
        var g = c.createRadialGradient(x, y, 0, x, y, r);
        g.addColorStop(0, 'rgba(' + b[2] + ',0.55)'); g.addColorStop(1, 'rgba(' + b[2] + ',0)');
        c.fillStyle = g; c.fillRect(0, 0, 480, 270);
      }
      c.globalCompositeOperation = 'source-over';
    },
    waves: function (c, t) {
      var g = c.createLinearGradient(0, 0, 0, 270);
      g.addColorStop(0, '#0A1A3A'); g.addColorStop(1, '#020611');
      c.fillStyle = g; c.fillRect(0, 0, 480, 270);
      var layers = [['30,120,220', 0.35, 150, 22, 0.012, 0.6], ['40,170,255', 0.28, 175, 18, 0.017, -0.8], ['90,90,240', 0.25, 200, 26, 0.009, 0.45], ['20,200,210', 0.22, 225, 14, 0.021, -1.1]];
      for (var i = 0; i < layers.length; i++) {
        var L = layers[i];
        c.beginPath(); c.moveTo(0, 270);
        for (var x = 0; x <= 480; x += 8) c.lineTo(x, L[2] + Math.sin(x * L[4] + t * L[5]) * L[3] + Math.sin(x * L[4] * 2.3 - t * L[5] * 0.7) * L[3] * 0.4);
        c.lineTo(480, 270); c.closePath();
        c.fillStyle = 'rgba(' + L[0] + ',' + L[1] + ')'; c.fill();
      }
    },
    stars: function (c, t) {
      if (!stars) stars = seeded(170, function (r, i) { return [((r * 977 + i * 0.37) % 1) * 480, ((r * 313 + i * 0.61) % 1) * 270, 0.3 + ((r * 59) % 1) * 1.3, (r * 31) % 6.28]; });
      var g = c.createLinearGradient(0, 0, 0, 270);
      g.addColorStop(0, '#02030A'); g.addColorStop(1, '#0B1030');
      c.fillStyle = g; c.fillRect(0, 0, 480, 270);
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i], x = (s[0] + t * 2 * s[2]) % 480, a = 0.35 + 0.65 * Math.abs(Math.sin(t * 0.8 + s[3]));
        c.fillStyle = 'rgba(255,255,255,' + a.toFixed(2) + ')';
        c.fillRect(x, s[1], s[2], s[2]);
      }
      var p = (t * 0.12) % 1;   // a shooting star now and then
      if (p < 0.12) {
        var q = p / 0.12, sx = 80 + q * 260, sy = 30 + q * 90;
        var tail = c.createLinearGradient(sx - 40, sy - 14, sx, sy);
        tail.addColorStop(0, 'rgba(255,255,255,0)'); tail.addColorStop(1, 'rgba(255,255,255,' + (1 - q).toFixed(2) + ')');
        c.strokeStyle = tail; c.lineWidth = 1.2; c.beginPath(); c.moveTo(sx - 40, sy - 14); c.lineTo(sx, sy); c.stroke();
      }
    },
    fluid: function (c, t) {
      var h = (t * 8) % 360;
      var g = c.createLinearGradient(240 + Math.cos(t * 0.1) * 240, 0, 240 - Math.cos(t * 0.1) * 240, 270);
      g.addColorStop(0, 'hsl(' + h.toFixed(0) + ',70%,30%)');
      g.addColorStop(0.5, 'hsl(' + ((h + 60) % 360).toFixed(0) + ',65%,22%)');
      g.addColorStop(1, 'hsl(' + ((h + 140) % 360).toFixed(0) + ',70%,16%)');
      c.fillStyle = g; c.fillRect(0, 0, 480, 270);
    },
    bubbles: function (c, t) {
      if (!bubbles) bubbles = seeded(26, function (r, i) { return [((r * 733 + i * 0.29) % 1) * 480, ((r * 211) % 1) * 400, 12 + ((r * 97) % 1) * 46, 4 + ((r * 13) % 1) * 9]; });
      var g = c.createLinearGradient(0, 0, 0, 270);
      g.addColorStop(0, '#1B0F3A'); g.addColorStop(1, '#07122B');
      c.fillStyle = g; c.fillRect(0, 0, 480, 270);
      c.globalCompositeOperation = 'lighter';
      for (var i = 0; i < bubbles.length; i++) {
        var b = bubbles[i], y = 300 - ((b[1] + t * b[3]) % 400), x = b[0] + Math.sin(t * 0.3 + i) * 12;
        var r = c.createRadialGradient(x, y, 0, x, y, b[2]);
        r.addColorStop(0, 'rgba(160,120,255,0.20)'); r.addColorStop(0.7, 'rgba(90,160,255,0.10)'); r.addColorStop(1, 'rgba(90,160,255,0)');
        c.fillStyle = r; c.beginPath(); c.arc(x, y, b[2], 0, 6.2832); c.fill();
      }
      c.globalCompositeOperation = 'source-over';
    }
  };

  function frame(now) {
    raf = 0;
    if (!current || current[2] !== 'anim' || document.hidden) return;
    if (now - last >= 33) {   // 30 frames a second is plenty for something this slow
      var dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      last = now;
      t += dt * (SPEEDS[pref('wallSpeed', 'normal')] || 1);
      DRAW[current[0]](ctx, t);
    }
    raf = window.requestAnimationFrame(frame);
  }
  function run() { if (!raf) { last = 0; raf = window.requestAnimationFrame(frame); } }
  function stop() { if (raf) window.cancelAnimationFrame(raf); raf = 0; }

  // MARK: - Pictures and videos from the Fundos folder

  function showPicture(i) {
    var url = mine.images[i % mine.images.length];
    var front = imgs[slide % 2], back = imgs[(slide + 1) % 2];
    back.style.backgroundImage = 'url("' + url + '")';
    back.style.opacity = '1';
    front.style.opacity = '0';
    slide++;
  }

  function load(done) {
    TV.wallpapers(function (res) {
      if (res) mine = {images: res.images || [], videos: res.videos || []};
      if (done) done();
    });
  }

  // MARK: - Applying the choice

  function apply() {
    make();
    var k = key(), c = byKey(k);
    current = c;
    stop();
    clearInterval(slideTimer); slideTimer = 0;
    var on = c[2] !== 'default';
    var cls = document.body.className.replace(/\s*wall-on/g, '');
    document.body.className = on ? cls + ' wall-on' : cls;
    box.style.display = on ? 'block' : 'none';
    canvas.style.display = c[2] === 'anim' ? 'block' : 'none';
    video.style.display = c[2] === 'video' ? 'block' : 'none';
    for (var i = 0; i < 2; i++) imgs[i].style.display = c[2] === 'mine' ? 'block' : 'none';
    if (c[2] !== 'video' && !video.paused) { try { video.pause(); } catch (e) {} }
    box.style.background = '';
    if (c[2] === 'still') {
      box.style.background = 'linear-gradient(160deg, ' + c[4][0] + ', ' + c[4][1] + ' 55%, ' + c[4][2] + ')';
    } else if (c[2] === 'anim') {
      DRAW[c[0]](ctx, t);
      run();
    } else if (c[2] === 'mine') {
      showPicture(0);
      var every = pref('wallEvery', 5);
      if (mine.images.length > 1) slideTimer = setInterval(function () { if (!document.hidden) showPicture(slide); }, every * 60000);
    } else if (c[2] === 'video') {
      var src = mine.videos[0];
      if (video.getAttribute('src') !== src) video.setAttribute('src', src);
      try { var p = video.play(); if (p && p.catch) p.catch(function () {}); } catch (e) {}
    }
    var blur = pref('wallBlur', 'off');
    var px = blur === 'strong' ? 22 : blur === 'soft' ? 8 : 0;
    var filter = px ? 'blur(' + px + 'px)' : '';
    canvas.style.filter = canvas.style.webkitFilter = filter;
    video.style.filter = video.style.webkitFilter = filter;
    for (var j = 0; j < 2; j++) imgs[j].style.filter = imgs[j].style.webkitFilter = filter;
    var darken = pref('wallDark', 25);
    shade.style.background = c[3] === false ? 'rgba(255,255,255,' + (darken / 100) + ')' : 'rgba(0,0,0,' + (darken / 100) + ')';
  }

  return {
    /** Reads the Fundos folder (on the PC), then shows the chosen background. */
    start: function (done) { if (TV.name !== 'pc') { if (done) done(); return; } load(function () { apply(); if (done) done(); }); },
    apply: apply,
    reload: function (done) { load(function () { apply(); if (done) done(); }); },
    choices: choices,
    key: key,
    name: function (k) { return byKey(k)[1]; },
    animated: function () { return byKey(key())[2] === 'anim'; },
    /** A background of ours is on: the picks' photo behind the screen gives way to it. */
    active: function () { return TV.name === 'pc' && key() !== 'default'; },
    /** White text over it (true), dark text (false), or no say (null: the time of day decides, as before). */
    dark: function () { return TV.name === 'pc' ? byKey(key())[3] : null; },
    pictures: function () { return mine.images.length; },
    media: function () { return mine.images.length + mine.videos.length; },
    /** For the long test run: whether the animation is drawing. */
    running: function () { return !!raf; }
  };
})();
