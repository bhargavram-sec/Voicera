// ── CURSOR ──
(function () {
    const c = document.getElementById('cursor'), d = document.getElementById('cursor-dot');
    if (!c || !d) return;
    let mx = 0, my = 0, rx = 0, ry = 0;
    document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; d.style.left = mx + 'px'; d.style.top = my + 'px' });
    (function t() { rx += (mx - rx) * .13; ry += (my - ry) * .13; c.style.left = rx + 'px'; c.style.top = ry + 'px'; requestAnimationFrame(t) })();
})();

// ── HERO WAVE ──
window.addEventListener('load', () => {
    const cv = document.getElementById('hero-canvas');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    function r() { const dpr = window.devicePixelRatio || 1; cv.width = cv.offsetWidth * dpr; cv.height = cv.offsetHeight * dpr; ctx.scale(dpr, dpr) }
    r(); window.addEventListener('resize', r); let ph = 0;
    (function draw() {
        const W = cv.offsetWidth, H = cv.offsetHeight; ctx.clearRect(0, 0, W, H);
        ctx.globalCompositeOperation = 'screen';
        const colors = ['rgba(0,113,227,', 'rgba(175,82,222,', 'rgba(255,41,117,', 'rgba(0,113,227,'];
        for (let l = 0; l < 4; l++) {
            const amp = 24 - l * 4, freq = 0.008 + l * .0025, phase = l * Math.PI / 2.8;
            ctx.beginPath();
            for (let x = 0; x <= W; x++) {
                const y = H / 2 + Math.sin(x * freq + ph + phase) * amp + Math.sin(x * freq * 2.2 - ph * .75 + phase) * (amp * .38);
                x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `${colors[l]}${.75 - l * .15})`; 
            ctx.lineWidth = 2.4 - l * .4; 
            ctx.shadowBlur = 10 - l * 2;
            ctx.shadowColor = ctx.strokeStyle;
            ctx.stroke();
        }
        ph += 0.026; requestAnimationFrame(draw);
    })();
});

// ── STUDIO WAVE ──
window.addEventListener('load', () => {
    const cv = document.getElementById('studio-canvas');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    function r() { const dpr = window.devicePixelRatio || 1; cv.width = cv.offsetWidth * dpr; cv.height = cv.offsetHeight * dpr; ctx.scale(dpr, dpr) }
    r(); window.addEventListener('resize', r); let ph = 0;
    (function draw() {
        const W = cv.offsetWidth, H = cv.offsetHeight; ctx.clearRect(0, 0, W, H);
        const cy = H * 0.3; // Center it visually behind "Right now"
        const g = ctx.createRadialGradient(W / 2, cy, 10, W / 2, cy, Math.min(W, H) * .4);
        g.addColorStop(0, 'rgba(175,82,222,.07)'); g.addColorStop(1, 'transparent');
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
        for (let r = 0; r < 4; r++) {
            const base = 38 + r * 28, pulse = Math.sin(ph + r * 1.08) * 7;
            ctx.beginPath(); ctx.arc(W / 2, cy, base + pulse, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(175,82,222,${.48 - r * .09})`; ctx.lineWidth = 1.2 - r * .22; ctx.stroke();
        }
        const bars = 20, bw = 9, gap = 5, total = bars * (bw + gap) - gap, sx = (W - total) / 2;
        for (let b = 0; b < bars; b++) {
            const bh = 14 + Math.abs(Math.sin(ph * 2.4 + b * .52)) * 58;
            const x = sx + b * (bw + gap), y = cy - bh / 2;
            ctx.fillStyle = `rgba(175,82,222,${.38 + .38 * Math.abs(Math.sin(ph + b * .42))})`;
            ctx.beginPath(); const rr = 3;
            ctx.moveTo(x + rr, y); ctx.lineTo(x + bw - rr, y); ctx.arcTo(x + bw, y, x + bw, y + rr, rr);
            ctx.lineTo(x + bw, y + bh - rr); ctx.arcTo(x + bw, y + bh, x + bw - rr, y + bh, rr);
            ctx.lineTo(x + rr, y + bh); ctx.arcTo(x, y + bh, x, y + bh - rr, rr);
            ctx.lineTo(x, y + rr); ctx.arcTo(x, y, x + rr, y, rr); ctx.closePath(); ctx.fill();
        }
        ph += 0.024; requestAnimationFrame(draw);
    })();
});

// ── SEQUENCE CANVAS LOGIC ──
const frameCount = 7;
const images = [];
const seqState = { frame: 0 };
let seqCtx = null;
let seqCanvas = null;

// Preload the 7 frames
const frameFilenames = [
    '001.jpeg', '002.png', '003.png', '004.png',
    '006.png', '007.png', '008.jpeg'
];

for (let i = 0; i < frameCount; i++) {
    const img = new Image();
    img.src = `/static/frames/${frameFilenames[i]}`;
    images.push(img);
}

function renderSeq() {
    if (!seqCtx || !images[seqState.frame]) return;
    const img = images[Math.round(seqState.frame)];
    if (!img || !img.complete) return;
    
    // Draw image maintaining aspect ratio and covering the canvas (object-fit: cover equivalent)
    const W = seqCanvas.width / (window.devicePixelRatio || 1);
    const H = seqCanvas.height / (window.devicePixelRatio || 1);
    
    let scale = Math.max(W / img.width, H / img.height);
    
    const isShifted = img.src.includes('003.png') || img.src.includes('007.png');
    if (img.src.includes('003.png')) {
        scale *= 1.15; // Zoom out slightly specifically for 003.png
    } else if (img.src.includes('007.png')) {
        scale *= 1.25; // Original zoom for 007.png
    }
    
    let x = (W / 2) - (img.width / 2) * scale;
    const y = (H / 2) - (img.height / 2) * scale;
    
    // Shift left slightly to prevent cropping/clashing with text overlay
    if (isShifted) {
        x -= W * 0.12; // 12% shift to the left
    }
    
    seqCtx.clearRect(0, 0, W, H);
    seqCtx.drawImage(img, x, y, img.width * scale, img.height * scale);
}

window.addEventListener('load', () => {
    seqCanvas = document.getElementById('seq-canvas');
    if (!seqCanvas) return;
    seqCtx = seqCanvas.getContext('2d');
    
    function resizeSeq() {
        const dpr = window.devicePixelRatio || 1;
        const parent = seqCanvas.parentElement;
        seqCanvas.width = parent.offsetWidth * dpr;
        seqCanvas.height = parent.offsetHeight * dpr;
        seqCtx.scale(dpr, dpr);
        renderSeq();
    }
    
    window.addEventListener('resize', resizeSeq);
    setTimeout(resizeSeq, 100);
});

// ── SCENE SWITCH ──
// ── SCENE SWITCH ──
let curScene = 0;
function goScene(n) {
    if (n < 0 || n > 6 || n === curScene) return; curScene = n;
    for (let i = 0; i < 7; i++) {
        const sb = document.getElementById('sb' + i);
        const sd = document.querySelectorAll('.sdot')[i];
        if (sb) sb.classList.toggle('on', i === n);
        if (sd) sd.classList.toggle('on', i === n);
    }
}


// ── GSAP ──
document.addEventListener('DOMContentLoaded', () => {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
    gsap.registerPlugin(ScrollTrigger);

    // Showcase scroll — advance scene smoothly over 7 frames
    const scenes = 7;
    gsap.to(seqState, {
        frame: frameCount - 1,
        snap: "frame",
        ease: "none",
        scrollTrigger: {
            trigger: '#showcase-wrap',
            start: 'top top',
            end: '+=' + (window.innerHeight * 2.5), // Greatly compressed scroll space for faster snapping
            scrub: 0.4, // Lower float delay for punchy reactions

            onUpdate: (self) => {
                // Determine scene directly from the scrubbed/lagged frame value, not instantaneous scroll
                const s = Math.min(scenes - 1, Math.round(seqState.frame));
                goScene(s);
                renderSeq();
            }
        }
    });
});


// ── DECEPTION AUDIO ──
let decPlaying = false;
const aEn = new Audio('/static/audio/demo_en.mp3');
const aHi = new Audio('/static/audio/demo_hi.mp3');
aEn.preload = aHi.preload = 'auto';
function playDeception() {
    if (decPlaying) return; decPlaying = true;
    const btn = document.getElementById('dec-btn'), st = document.getElementById('dec-status');
    if (!btn || !st) return;
    btn.style.opacity = '.5'; btn.style.pointerEvents = 'none';
    st.textContent = 'Playing — English…';
    aEn.play().catch(() => { });
    setTimeout(() => { aEn.pause(); aEn.currentTime = 0; st.textContent = 'Switching to Hindi…'; aHi.play().catch(() => { }) }, 3200);
    setTimeout(() => { aHi.pause(); aHi.currentTime = 0; st.textContent = 'You just heard Voicera. ✦'; st.style.color = 'rgba(0,113,227,.8)'; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto'; decPlaying = false }, 6500);
}

// ── POPULATION ──
const POP = { hi: { n: 1400000000, l: 'Hindi speakers' }, ta: { n: 90000000, l: 'Tamil speakers' }, te: { n: 95000000, l: 'Telugu speakers' }, kn: { n: 60000000, l: 'Kannada speakers' }, ml: { n: 38000000, l: 'Malayalam speakers' }, en: { n: 1500000000, l: 'English speakers' }, es: { n: 500000000, l: 'Spanish speakers' }, fr: { n: 300000000, l: 'French speakers' }, de: { n: 135000000, l: 'German speakers' }, ja: { n: 125000000, l: 'Japanese speakers' }, zh: { n: 1100000000, l: 'Mandarin speakers' }, ar: { n: 420000000, l: 'Arabic speakers' }, pt: { n: 260000000, l: 'Portuguese speakers' }, ru: { n: 258000000, l: 'Russian speakers' }, ko: { n: 77000000, l: 'Korean speakers' } };

// ── STATE ──
let selLang = 'hi', selGender = 'female', curMode = 'video';
let pollTimer = null, hmTimer = null, fpRaf = null;

function selectLanguage(c) { 
    selLang = c; 
    const input = document.getElementById('selectedLang');
    if (input) input.value = c; 
    document.querySelectorAll('.lc').forEach(b => b.classList.toggle('on', b.dataset.value === c)) 
}
function selectGender(g) { 
    selGender = g; 
    const input = document.getElementById('selectedGender');
    if (input) input.value = g; 
    const btnF = document.getElementById('btnFemale');
    const btnM = document.getElementById('btnMale');
    if (btnF) btnF.classList.toggle('on', g === 'female'); 
    if (btnM) btnM.classList.toggle('on', g === 'male') 
}
function switchMode(m) {
    curMode = m;
    ['video', 'audio', 'url'].forEach(mode => {
        const k = mode.charAt(0).toUpperCase() + mode.slice(1);
        const mEl = document.getElementById('mode' + k);
        const tEl = document.getElementById('tab' + k);
        if (mEl) mEl.classList.toggle('hidden', mode !== m);
        if (tEl) tEl.classList.toggle('on', mode === m);
    });
}

// Event Listeners for inputs
document.addEventListener('DOMContentLoaded', () => {
    const vIn = document.getElementById('videoInput');
    if (vIn) vIn.addEventListener('change', function () { 
        const e = document.getElementById('videoNameDisplay'); 
        if (e) {
            e.textContent = this.files[0]?.name || ''; 
            e.style.display = this.files[0] ? 'inline-block' : 'none' 
        }
    });

    const aIn = document.getElementById('audioInput');
    if (aIn) aIn.addEventListener('change', function () { 
        const e = document.getElementById('audioNameDisplay'); 
        if (e) {
            e.textContent = this.files[0]?.name || ''; 
            e.style.display = this.files[0] ? 'inline-block' : 'none' 
        }
    });
});

// ── FINGERPRINT ──
let fpPh = 0;
function startFP() {
    const cv = document.getElementById('fp-c');
    if (!cv) return;
    const ctx = cv.getContext('2d'), dpr = window.devicePixelRatio || 1;
    cv.width = cv.offsetWidth * dpr; cv.height = cv.offsetHeight * dpr; ctx.scale(dpr, dpr);
    function draw() {
        const W = cv.offsetWidth, H = cv.offsetHeight, cx = W / 2, cy = H / 2, base = Math.min(W, H) * .27;
        ctx.clearRect(0, 0, W, H);
        const pbFill = document.getElementById('pb-fill');
        const pct = pbFill ? parseFloat(pbFill.style.width || '0') / 100 : 0;
        const pts = 120;
        ctx.beginPath();
        for (let i = 0; i <= pts; i++) { const a = (i / pts) * Math.PI * 2, n = Math.sin(a * 7 + fpPh) * 8 + Math.sin(a * 13 - fpPh * .9) * 4 + Math.sin(a * 2 + fpPh * 1.4) * 9; const r = base + n, x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r; i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y) }
        ctx.closePath(); ctx.strokeStyle = 'rgba(0,113,227,.48)'; ctx.lineWidth = 1.4; ctx.stroke(); ctx.fillStyle = 'rgba(0,113,227,.03)'; ctx.fill();
        if (pct > .12) {
            const ib = base * (.42 + pct * .28);
            ctx.beginPath();
            for (let i = 0; i <= pts; i++) { const a = (i / pts) * Math.PI * 2, n = Math.sin(a * 4 - fpPh * 1.2) * 5 + Math.sin(a * 9 + fpPh * .6) * 3; const r = ib + n, x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r; i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y) }
            ctx.closePath(); ctx.strokeStyle = `rgba(175,82,222,${.22 + pct * .48})`; ctx.lineWidth = .9; ctx.stroke(); ctx.fillStyle = `rgba(175,82,222,${.02 + pct * .04})`; ctx.fill();
        }
        ctx.beginPath(); ctx.arc(cx, cy, 2.2, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,113,227,.85)'; ctx.fill();
        ctx.font = '9px DM Sans,sans-serif'; ctx.textAlign = 'center';
        ctx.fillStyle = 'rgba(255,255,255,.22)'; ctx.fillText('Original Voice', cx, cy - base - 10);
        if (pct > .12) { ctx.fillStyle = 'rgba(175,82,222,.45)'; ctx.fillText('Dubbed Voice', cx, cy + 7) }
        fpPh += 0.017; fpRaf = requestAnimationFrame(draw);
    }
    draw();
}
function stopFP() { if (fpRaf) cancelAnimationFrame(fpRaf) }

// ── HEATMAP ──
const HMW = [{ w: 'Welcome', c: .98 }, { w: 'to', c: .99 }, { w: 'this', c: .95 }, { w: 'machine', c: .92 }, { w: 'learning', c: .89 }, { w: 'tutorial', c: .85 }, { w: 'covering', c: .91 }, { w: 'neural', c: .83 }, { w: 'networks', c: .8 }, { w: 'and', c: .99 }, { w: 'deep', c: .88 }, { w: 'learning', c: .74 }, { w: 'concepts', c: .71 }];
let hmIdx = 0;
function startHM() {
    hmIdx = 0; 
    const hmContainer = document.getElementById('hm-words');
    if (hmContainer) hmContainer.innerHTML = '';
    hmTimer = setInterval(() => {
        if (hmIdx < HMW.length) {
            const d = HMW[hmIdx++];
            const s = document.createElement('span');
            s.className = 'hw ' + (d.c > .9 ? 'hw-hi' : d.c > .76 ? 'hw-md' : 'hw-lo');
            s.textContent = d.w + ' '; s.title = Math.round(d.c * 100) + '% confidence';
            if (hmContainer) hmContainer.appendChild(s);
        } else {
            clearInterval(hmTimer);
            const avg = HMW.reduce((a, d) => a + d.c, 0) / HMW.length;
            const pctEl = document.getElementById('mn-pct');
            if (pctEl) pctEl.textContent = Math.round(avg * 100) + '%';
        }
    }, 400);
}

// ── REACH COUNTER ──
function animateReach() {
    const data = POP[selLang] || { n: 50000000, l: 'speakers' };
    const label = document.getElementById('reach-l');
    if (label) label.textContent = data.l;
    const el = document.getElementById('reach-n');
    if (!el) return;
    const t0 = performance.now(), dur = 2800;
    (function tick(now) { const p = Math.min((now - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3); el.textContent = Math.round(e * data.n).toLocaleString('en-IN'); if (p < 1) requestAnimationFrame(tick) })(t0);
}

// ── VIEWS ──
function showView(id) { ['uploadView', 'processView', 'resultView', 'errorView'].forEach(v => {
    const el = document.getElementById(v);
    if (el) el.classList.toggle('hidden', v !== id);
}) }
function setProgress(pct) { 
    const el = document.getElementById('pb-fill');
    if (el) el.style.width = pct + '%' 
}
function updateSteps(pct) {
    [{ id: 'step1', t: 10 }, { id: 'step2', t: 25 }, { id: 'step3', t: 45 }, { id: 'step4', t: 65 }].forEach(s => {
        const el = document.getElementById(s.id);
        if (!el) return;
        if (pct >= s.t + 15) { 
            el.className = 'sr done'; 
            const dot = el.querySelector('.sc-dot');
            if (dot) dot.textContent = '✓' 
        }
        else if (pct >= s.t) { el.className = 'sr active' }
    });
}

// ── START ──
async function startProcess() {
    const syncInp = document.getElementById('syncMode');
    const audioInp = document.getElementById('audioOnly');
    const srcInp = document.getElementById('sourceLang');
    const urlInp = document.getElementById('urlInput');

    const syncMode = syncInp ? syncInp.checked : false;
    const audioOnly = audioInp ? audioInp.checked : false;
    const srcLang = srcInp ? srcInp.value : 'auto';
    
    let jobId;
    try {
        if (curMode === 'url') {
            const url = urlInp ? urlInp.value.trim() : '';
            if (!url) { alert('Please enter a URL.'); return }
            const r = await fetch('/api/upload-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url, language: selLang, gender: selGender, sync_mode: syncMode, source_lang: srcLang, audio_only: audioOnly, model_size: 'medium' }) });
            const d = await r.json(); if (!d.success) { showView('errorView'); const errEl = document.getElementById('err-msg'); if (errEl) errEl.textContent = d.error; return } jobId = d.job_id;
        } else {
            const vIn = document.getElementById('videoInput');
            const aIn = document.getElementById('audioInput');
            const inp = curMode === 'video' ? vIn : aIn;
            if (!inp || !inp.files[0]) { alert('Please select a file.'); return }
            const fd = new FormData(); fd.append('video', inp.files[0]); fd.append('language', selLang); fd.append('gender', selGender); fd.append('sync_mode', syncMode); fd.append('source_lang', srcLang); fd.append('audio_only', audioOnly); fd.append('model_size', 'medium');
            const r = await fetch('/api/upload', { method: 'POST', body: fd }); const d = await r.json(); if (!d.success) { showView('errorView'); const errEl = document.getElementById('err-msg'); if (errEl) errEl.textContent = d.error; return } jobId = d.job_id;
        }
    } catch (e) { showView('errorView'); const errEl = document.getElementById('err-msg'); if (errEl) errEl.textContent = e.message; return }
    showView('processView'); startFP(); startHM(); poll(jobId);
}

// ── POLL ──
function poll(jobId) {
    pollTimer = setInterval(async () => {
        try {
            const r = await fetch('/api/status/' + jobId); const job = await r.json();
            const pct = job.progress || 0; setProgress(pct); updateSteps(pct);
            const procT = document.getElementById('proc-t');
            if (job.current_step && procT) procT.textContent = job.current_step + '…';
            if (job.status === 'completed') { clearInterval(pollTimer); clearInterval(hmTimer); stopFP(); onDone(job) }
            else if (job.status === 'failed') { 
                clearInterval(pollTimer); clearInterval(hmTimer); stopFP(); 
                showView('errorView'); 
                const errEl = document.getElementById('err-msg');
                if (errEl) errEl.textContent = job.error || 'Unknown error' 
            }
        } catch (e) { console.error(e) }
    }, 2000);
}

// ── ON DONE ──
function onDone(job) {
    showView('resultView'); 
    setTimeout(animateReach, 300);
    if (job.output_path) { 
        const url = '/api/download/' + job.output_path; 
        const player = document.getElementById('preview-player');
        const dlBtn = document.getElementById('dl-btn');
        if (player) player.src = url; 
        if (dlBtn) dlBtn.href = url 
    }
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
    const f = document.querySelector('.lc'); 
    if (f) { 
        f.classList.add('on'); 
        selLang = f.dataset.value;
        const input = document.getElementById('selectedLang');
        if (input) input.value = selLang;
    }
});
