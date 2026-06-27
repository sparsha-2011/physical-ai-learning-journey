<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenUSD Certification Study — README</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

  :root {
    --black: #0A0A0F;
    --dark: #12121A;
    --dark2: #1A1A26;
    --dark3: #22222F;
    --nvidia: #76B900;
    --teal: #00D4AA;
    --amber: #F5A623;
    --purple: #8B7FE8;
    --coral: #FF6B6B;
    --offwhite: #E8E6DE;
    --muted: #6B6B7E;
    --border: rgba(255,255,255,0.07);
    --mono: 'JetBrains Mono', monospace;
    --sans: 'Inter', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body { background: var(--black); color: var(--offwhite); font-family: var(--sans); line-height: 1.7; overflow-x: hidden; }

  /* ── HERO ── */
  .hero {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    position: relative;
    text-align: center;
    overflow: hidden;
  }

  /* animated gradient grid background */
  .hero-bg {
    position: absolute;
    inset: 0;
    background:
      linear-gradient(rgba(118,185,0,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(118,185,0,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    animation: gridDrift 20s linear infinite;
  }
  @keyframes gridDrift { from { background-position: 0 0; } to { background-position: 60px 60px; } }

  /* radial glow */
  .hero-glow {
    position: absolute;
    width: 800px;
    height: 800px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(118,185,0,0.08) 0%, rgba(0,212,170,0.04) 40%, transparent 70%);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation: pulse 4s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100%{opacity:.6;transform:translate(-50%,-50%) scale(1)} 50%{opacity:1;transform:translate(-50%,-50%) scale(1.05)} }

  .hero-content { position: relative; z-index: 2; max-width: 800px; }

  .hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(118,185,0,0.1);
    border: 1px solid rgba(118,185,0,0.25);
    border-radius: 999px;
    padding: 6px 16px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--nvidia);
    letter-spacing: .08em;
    margin-bottom: 2rem;
  }
  .hero-eyebrow::before { content: '◆'; font-size: 8px; }

  .hero-title {
    font-family: var(--mono);
    font-size: clamp(2.2rem, 6vw, 4rem);
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 1rem;
    letter-spacing: -.02em;
  }
  .hero-title .word-usd { color: var(--nvidia); }
  .hero-title .word-cert { color: var(--teal); }

  .hero-sub {
    font-size: 16px;
    color: var(--muted);
    max-width: 540px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
  }
  .hero-sub strong { color: var(--offwhite); font-weight: 500; }

  /* cert badge */
  .cert-badge {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: linear-gradient(135deg, rgba(118,185,0,0.15), rgba(0,212,170,0.08));
    border: 1px solid rgba(118,185,0,0.3);
    border-radius: 12px;
    padding: 14px 24px;
    margin-bottom: 3rem;
  }
  .cert-badge-icon { font-size: 28px; }
  .cert-badge-text { text-align: left; }
  .cert-badge-title { font-family: var(--mono); font-size: 13px; font-weight: 600; color: var(--nvidia); letter-spacing:.04em; }
  .cert-badge-sub { font-size: 12px; color: var(--muted); }

  /* stats row */
  .hero-stats {
    display: flex;
    gap: 2rem;
    justify-content: center;
    flex-wrap: wrap;
  }
  .stat { text-align: center; }
  .stat-num { font-family: var(--mono); font-size: 2rem; font-weight: 700; color: var(--nvidia); line-height: 1; }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-top: 4px; }

  /* ── LAYER STACK DIAGRAM ── */
  .stack-section {
    padding: 5rem 2rem;
    max-width: 900px;
    margin: 0 auto;
  }
  .section-eyebrow {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--nvidia);
    letter-spacing: .1em;
    text-transform: uppercase;
    margin-bottom: .75rem;
  }
  .section-title {
    font-family: var(--mono);
    font-size: clamp(1.4rem, 3vw, 2rem);
    font-weight: 700;
    margin-bottom: .75rem;
    line-height: 1.2;
  }
  .section-desc { font-size: 15px; color: var(--muted); max-width: 560px; margin-bottom: 3rem; line-height: 1.7; }

  /* animated layer stack */
  .layer-stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 2rem 0;
  }
  .layer {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 20px;
    border-radius: 10px;
    border: 1px solid;
    animation: slideIn .5s ease both;
    cursor: default;
    transition: transform .2s, box-shadow .2s;
  }
  .layer:hover { transform: translateX(6px); }
  @keyframes slideIn { from { opacity:0; transform:translateX(-20px); } to { opacity:1; transform:translateX(0); } }
  .layer:nth-child(1) { animation-delay:.1s; background:rgba(118,185,0,0.06); border-color:rgba(118,185,0,0.25); }
  .layer:nth-child(2) { animation-delay:.2s; background:rgba(139,127,232,0.06); border-color:rgba(139,127,232,0.25); }
  .layer:nth-child(3) { animation-delay:.3s; background:rgba(0,212,170,0.06); border-color:rgba(0,212,170,0.25); }
  .layer:nth-child(4) { animation-delay:.4s; background:rgba(245,166,35,0.06); border-color:rgba(245,166,35,0.25); }
  .layer:nth-child(5) { animation-delay:.5s; background:rgba(255,107,107,0.06); border-color:rgba(255,107,107,0.25); }
  .layer-strength {
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    min-width: 68px;
    text-align: center;
    letter-spacing:.04em;
  }
  .layer:nth-child(1) .layer-strength { background:rgba(118,185,0,0.2); color:var(--nvidia); }
  .layer:nth-child(2) .layer-strength { background:rgba(139,127,232,0.2); color:var(--purple); }
  .layer:nth-child(3) .layer-strength { background:rgba(0,212,170,0.2); color:var(--teal); }
  .layer:nth-child(4) .layer-strength { background:rgba(245,166,35,0.2); color:var(--amber); }
  .layer:nth-child(5) .layer-strength { background:rgba(255,107,107,0.2); color:var(--coral); }
  .layer-name { font-family: var(--mono); font-size: 14px; font-weight: 600; flex: 1; }
  .layer:nth-child(1) .layer-name { color:var(--nvidia); }
  .layer:nth-child(2) .layer-name { color:var(--purple); }
  .layer:nth-child(3) .layer-name { color:var(--teal); }
  .layer:nth-child(4) .layer-name { color:var(--amber); }
  .layer:nth-child(5) .layer-name { color:var(--coral); }
  .layer-desc { font-size: 13px; color: var(--muted); }
  .layer-arrow { font-size: 12px; color: var(--muted); }

  /* composed result */
  .composed {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(118,185,0,0.12), rgba(0,212,170,0.06));
    border: 1px solid rgba(118,185,0,0.4);
    margin-top: 4px;
  }
  .composed-label { font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--nvidia); background:rgba(118,185,0,0.15); padding:3px 10px; border-radius:4px; letter-spacing:.04em; }
  .composed-text { font-family: var(--mono); font-size: 14px; color: var(--offwhite); font-weight: 500; }

  /* ── LIVERPS SECTION ── */
  .liverps-section {
    padding: 5rem 2rem;
    background: var(--dark);
  }
  .liverps-inner { max-width: 900px; margin: 0 auto; }

  .liverps-grid {
    display: grid;
    grid-template-columns: repeat(6,1fr);
    gap: 10px;
    margin-top: 2rem;
  }
  .liverps-card {
    border-radius: 12px;
    padding: 1.25rem .75rem;
    text-align: center;
    border: 1px solid;
    transition: transform .2s, box-shadow .2s;
    cursor: default;
  }
  .liverps-card:hover { transform: translateY(-4px); }
  .liverps-card .l-letter { font-family: var(--mono); font-size: 2rem; font-weight: 800; line-height: 1; margin-bottom: .4rem; }
  .liverps-card .l-name { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; margin-bottom: .4rem; }
  .liverps-card .l-desc { font-size: 11px; line-height: 1.4; }
  .liverps-card.c1 { background:rgba(118,185,0,0.07); border-color:rgba(118,185,0,0.25); }
  .liverps-card.c1 .l-letter,.liverps-card.c1 .l-name{color:var(--nvidia)}
  .liverps-card.c1 .l-desc{color:rgba(118,185,0,0.7)}
  .liverps-card.c2 { background:rgba(0,212,170,0.07); border-color:rgba(0,212,170,0.25); }
  .liverps-card.c2 .l-letter,.liverps-card.c2 .l-name{color:var(--teal)}
  .liverps-card.c2 .l-desc{color:rgba(0,212,170,0.7)}
  .liverps-card.c3 { background:rgba(245,166,35,0.07); border-color:rgba(245,166,35,0.25); }
  .liverps-card.c3 .l-letter,.liverps-card.c3 .l-name{color:var(--amber)}
  .liverps-card.c3 .l-desc{color:rgba(245,166,35,0.7)}
  .liverps-card.c4 { background:rgba(255,107,107,0.07); border-color:rgba(255,107,107,0.25); }
  .liverps-card.c4 .l-letter,.liverps-card.c4 .l-name{color:var(--coral)}
  .liverps-card.c4 .l-desc{color:rgba(255,107,107,0.7)}
  .liverps-card.c5 { background:rgba(139,127,232,0.07); border-color:rgba(139,127,232,0.25); }
  .liverps-card.c5 .l-letter,.liverps-card.c5 .l-name{color:var(--purple)}
  .liverps-card.c5 .l-desc{color:rgba(139,127,232,0.7)}
  .liverps-card.c6 { background:rgba(255,255,255,0.04); border-color:rgba(255,255,255,0.1); }
  .liverps-card.c6 .l-letter,.liverps-card.c6 .l-name{color:var(--muted)}
  .liverps-card.c6 .l-desc{color:rgba(255,255,255,0.3)}

  /* ── STUDY PLAN ── */
  .plan-section {
    padding: 5rem 2rem;
    max-width: 900px;
    margin: 0 auto;
  }
  .plan-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 2rem;
  }
  .plan-card {
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    border: 1px solid var(--border);
    background: var(--dark2);
    display: flex;
    gap: 14px;
    align-items: flex-start;
    transition: border-color .2s, background .2s;
  }
  .plan-card:hover { border-color: rgba(118,185,0,0.2); background: var(--dark3); }
  .plan-card.done { border-color: rgba(118,185,0,0.2); }
  .plan-card.active { border-color: rgba(0,212,170,0.3); background: rgba(0,212,170,0.04); }
  .plan-day {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    min-width: 38px;
    padding: 4px 0;
    color: var(--muted);
    letter-spacing:.04em;
  }
  .plan-info { flex: 1; }
  .plan-title { font-size: 14px; font-weight: 600; color: var(--offwhite); margin-bottom: 3px; }
  .plan-sub { font-size: 12px; color: var(--muted); }
  .plan-status {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    white-space: nowrap;
    align-self: flex-start;
    margin-top: 2px;
  }
  .status-done { background: rgba(118,185,0,0.15); color: var(--nvidia); }
  .status-active { background: rgba(0,212,170,0.15); color: var(--teal); }
  .status-soon { background: rgba(255,255,255,0.06); color: var(--muted); }

  /* ── CODE SHOWCASE ── */
  .code-section {
    padding: 5rem 2rem;
    background: var(--dark);
  }
  .code-inner { max-width: 900px; margin: 0 auto; }
  .code-window {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border);
    margin-top: 2rem;
    box-shadow: 0 40px 80px rgba(0,0,0,0.4);
  }
  .code-titlebar {
    background: #1E1E2E;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--border);
  }
  .dot { width: 12px; height: 12px; border-radius: 50%; }
  .dot-r { background: #FF5F57; }
  .dot-y { background: #FFBD2E; }
  .dot-g { background: #28CA41; }
  .code-filename {
    margin-left: 8px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
  }
  .code-body {
    background: #13131D;
    padding: 1.5rem;
    overflow-x: auto;
  }
  .code-body pre {
    font-family: var(--mono);
    font-size: 13px;
    line-height: 1.8;
    margin: 0;
  }
  .ck { color: #C586C0; }
  .cs { color: #CE9178; }
  .cn { color: #B5CEA8; }
  .cv { color: #9CDCFE; }
  .cp { color: #4EC9B0; }
  .cw { color: #DCDCAA; }
  .cm { color: #5A6A5A; font-style: italic; }
  .co { color: var(--offwhite); }

  /* ── DOMAINS ── */
  .domains-section {
    padding: 5rem 2rem;
    max-width: 900px;
    margin: 0 auto;
  }
  .domains-grid {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 12px;
    margin-top: 2rem;
  }
  .domain-card {
    border-radius: 12px;
    padding: 1.25rem;
    border: 1px solid var(--border);
    background: var(--dark2);
    text-align: center;
    transition: transform .2s;
  }
  .domain-card:hover { transform: translateY(-3px); }
  .domain-icon { font-size: 1.75rem; margin-bottom: .5rem; }
  .domain-name { font-family: var(--mono); font-size: 12px; font-weight: 600; margin-bottom: .25rem; }
  .domain-weight { font-size: 11px; font-weight: 700; }
  .domain-card:nth-child(1) { border-color:rgba(118,185,0,0.2); }
  .domain-card:nth-child(1) .domain-name { color:var(--nvidia); }
  .domain-card:nth-child(1) .domain-weight { color:var(--nvidia); }
  .domain-card:nth-child(2) { border-color:rgba(245,166,35,0.2); }
  .domain-card:nth-child(2) .domain-name { color:var(--amber); }
  .domain-card:nth-child(2) .domain-weight { color:var(--amber); }
  .domain-card:nth-child(3) { border-color:rgba(255,107,107,0.2); }
  .domain-card:nth-child(3) .domain-name { color:var(--coral); }
  .domain-card:nth-child(3) .domain-weight { color:var(--coral); }
  .domain-card:nth-child(4) { border-color:rgba(0,212,170,0.2); }
  .domain-card:nth-child(4) .domain-name { color:var(--teal); }
  .domain-card:nth-child(4) .domain-weight { color:var(--teal); }
  .domain-card:nth-child(5) { border-color:rgba(139,127,232,0.2); }
  .domain-card:nth-child(5) .domain-name { color:var(--purple); }
  .domain-card:nth-child(5) .domain-weight { color:var(--purple); }
  .domain-card:nth-child(6) { border-color:rgba(118,185,0,0.15); }
  .domain-card:nth-child(6) .domain-name { color:rgba(118,185,0,0.8); }
  .domain-card:nth-child(6) .domain-weight { color:rgba(118,185,0,0.8); }
  .domain-card:nth-child(7) { border-color:rgba(0,212,170,0.15); }
  .domain-card:nth-child(7) .domain-name { color:rgba(0,212,170,0.8); }
  .domain-card:nth-child(7) .domain-weight { color:rgba(0,212,170,0.8); }
  .domain-card:nth-child(8) { border-color:rgba(245,166,35,0.15); }
  .domain-card:nth-child(8) .domain-name { color:rgba(245,166,35,0.8); }
  .domain-card:nth-child(8) .domain-weight { color:rgba(245,166,35,0.8); }

  /* ── SETUP SECTION ── */
  .setup-section {
    padding: 5rem 2rem;
    background: var(--dark);
  }
  .setup-inner { max-width: 900px; margin: 0 auto; }
  .setup-steps {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 2rem;
  }
  .setup-step {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }
  .step-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(118,185,0,0.1);
    border: 1px solid rgba(118,185,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 700;
    color: var(--nvidia);
    flex-shrink: 0;
  }
  .step-body { flex: 1; padding-top: 4px; }
  .step-title { font-size: 14px; font-weight: 600; color: var(--offwhite); margin-bottom: 4px; }
  .step-cmd {
    display: inline-block;
    background: var(--dark3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--nvidia);
    margin-top: 4px;
  }

  /* ── FOOTER ── */
  .footer {
    padding: 4rem 2rem;
    text-align: center;
    border-top: 1px solid var(--border);
    position: relative;
  }
  .footer-glow {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 200px;
    background: radial-gradient(ellipse at bottom, rgba(118,185,0,0.06) 0%, transparent 70%);
    pointer-events: none;
  }
  .footer-title {
    font-family: var(--mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--nvidia);
    margin-bottom: .5rem;
  }
  .footer-sub { font-size: 14px; color: var(--muted); margin-bottom: 2rem; }
  .footer-tags { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
  .tag {
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 999px;
    border: 1px solid var(--border);
    color: var(--muted);
  }
  .tag.green { border-color: rgba(118,185,0,0.3); color: var(--nvidia); background: rgba(118,185,0,0.06); }
  .tag.teal { border-color: rgba(0,212,170,0.3); color: var(--teal); background: rgba(0,212,170,0.06); }

  /* divider */
  .divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    max-width: 900px;
    margin: 0 auto;
  }

  @media (max-width: 700px) {
    .liverps-grid { grid-template-columns: repeat(3,1fr); }
    .plan-grid { grid-template-columns: 1fr; }
    .domains-grid { grid-template-columns: repeat(2,1fr); }
    .hero-stats { gap: 1.5rem; }
  }
</style>
</head>
<body>

<!-- ══════════════ HERO ══════════════ -->
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-glow"></div>
  <div class="hero-content">

    <div class="hero-eyebrow">NCP · OpenUSD Development · Study Repository</div>

    <h1 class="hero-title">
      Open<span class="word-usd">USD</span><br>
      <span class="word-cert">Certification</span> Study
    </h1>

    <p class="hero-sub">
      A structured 10-day study system for the
      <strong>NVIDIA-Certified Professional: OpenUSD Development</strong> exam —
      covering all 8 domains with visual notes, hands-on code, and working USD scene files.
    </p>

    <div class="cert-badge">
      <div class="cert-badge-icon">🎯</div>
      <div class="cert-badge-text">
        <div class="cert-badge-title">NVIDIA-Certified Professional</div>
        <div class="cert-badge-sub">OpenUSD Development · Exam Prep</div>
      </div>
    </div>

    <div class="hero-stats">
      <div class="stat">
        <div class="stat-num">10</div>
        <div class="stat-label">Study Days</div>
      </div>
      <div class="stat">
        <div class="stat-num">8</div>
        <div class="stat-label">Exam Domains</div>
      </div>
      <div class="stat">
        <div class="stat-num">30+</div>
        <div class="stat-label">Hours of Study</div>
      </div>
      <div class="stat">
        <div class="stat-num">100%</div>
        <div class="stat-label">Hands-on Code</div>
      </div>
    </div>

  </div>
</section>


<!-- ══════════════ LAYER STACK DIAGRAM ══════════════ -->
<section class="stack-section">
  <div class="section-eyebrow">// Core concept</div>
  <h2 class="section-title">Composition in Action</h2>
  <p class="section-desc">USD's superpower — multiple layers of scene description composed into one final result. The layer listed first is the strongest. Its opinions always win.</p>

  <div class="layer-stack">
    <div class="layer">
      <span class="layer-strength">STRONGEST</span>
      <span class="layer-name">director_overrides.usda</span>
      <span class="layer-desc">final creative decisions — always wins</span>
      <span class="layer-arrow">↑</span>
    </div>
    <div class="layer">
      <span class="layer-strength">2nd</span>
      <span class="layer-name">anim.usda</span>
      <span class="layer-desc">keyframes &amp; motion — uses <code style="font-size:11px;opacity:.7">over</code></span>
      <span class="layer-arrow"></span>
    </div>
    <div class="layer">
      <span class="layer-strength">3rd</span>
      <span class="layer-name">lighting.usda</span>
      <span class="layer-desc">lights, sky, atmosphere</span>
      <span class="layer-arrow"></span>
    </div>
    <div class="layer">
      <span class="layer-strength">4th</span>
      <span class="layer-name">layout.usda</span>
      <span class="layer-desc">asset placement &amp; transforms</span>
      <span class="layer-arrow"></span>
    </div>
    <div class="layer">
      <span class="layer-strength">WEAKEST</span>
      <span class="layer-name">model.usda</span>
      <span class="layer-desc">base geometry — uses <code style="font-size:11px;opacity:.7">def</code></span>
      <span class="layer-arrow">↓</span>
    </div>
  </div>

  <div class="composed">
    <span class="composed-label">STAGE</span>
    <span class="composed-text">All 5 layers composed → one unified scene. Conflicts resolved by strength order.</span>
  </div>
</section>

<hr class="divider">

<!-- ══════════════ LIVERPS ══════════════ -->
<section class="liverps-section">
  <div class="liverps-inner">
    <div class="section-eyebrow">// Composition strength ordering</div>
    <h2 class="section-title">LIVERPS</h2>
    <p class="section-desc">The mnemonic that governs how USD resolves conflicting opinions. Local is always the strongest — it always wins.</p>

    <div class="liverps-grid">
      <div class="liverps-card c1">
        <div class="l-letter">L</div>
        <div class="l-name">Local</div>
        <div class="l-desc">Opinions authored directly in the layer stack. Always the strongest.</div>
      </div>
      <div class="liverps-card c2">
        <div class="l-letter">I</div>
        <div class="l-name">Inherits</div>
        <div class="l-desc">Broadcast opinions from a class prim to all inheriting prims.</div>
      </div>
      <div class="liverps-card c3">
        <div class="l-letter">V</div>
        <div class="l-name">Variants</div>
        <div class="l-desc">Switchable options on a prim — colour, LOD, on/off states.</div>
      </div>
      <div class="liverps-card c4">
        <div class="l-letter">R</div>
        <div class="l-name">References</div>
        <div class="l-desc">Graft a prim from another file. Always loaded eagerly.</div>
      </div>
      <div class="liverps-card c5">
        <div class="l-letter">P</div>
        <div class="l-name">Payloads</div>
        <div class="l-desc">Like references but lazy — loaded on demand for performance.</div>
      </div>
      <div class="liverps-card c6">
        <div class="l-letter">S</div>
        <div class="l-name">Specializes</div>
        <div class="l-desc">Weakest arc. Provides fallback defaults for material libraries.</div>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<!-- ══════════════ STUDY PLAN ══════════════ -->
<section class="plan-section">
  <div class="section-eyebrow">// 10-day structured curriculum</div>
  <h2 class="section-title">Study Plan</h2>
  <p class="section-desc">Each day has visual HTML notes, annotated Python code examples, and working .usda scene files you can open in usdview.</p>

  <div class="plan-grid">
    <div class="plan-card done">
      <div class="plan-day">DAY 01</div>
      <div class="plan-info">
        <div class="plan-title">USD Foundations</div>
        <div class="plan-sub">Stage · Prims · Properties · Metadata · File Formats</div>
      </div>
      <span class="plan-status status-done">✓ Done</span>
    </div>
    <div class="plan-card done">
      <div class="plan-day">DAY 02</div>
      <div class="plan-info">
        <div class="plan-title">Composition Part 1</div>
        <div class="plan-sub">Sublayers · References · Payloads · Value Resolution</div>
      </div>
      <span class="plan-status status-done">✓ Done</span>
    </div>
    <div class="plan-card done">
      <div class="plan-day">DAY 03</div>
      <div class="plan-info">
        <div class="plan-title">Composition Part 2</div>
        <div class="plan-sub">Variants · Inherits · Specializes · Encapsulation</div>
      </div>
      <span class="plan-status status-done">✓ Done</span>
    </div>
    <div class="plan-card active">
      <div class="plan-day">DAY 04</div>
      <div class="plan-info">
        <div class="plan-title">Composition Part 3</div>
        <div class="plan-sub">Advanced patterns · Flatten · Multi-user workflows</div>
      </div>
      <span class="plan-status status-active">▶ Active</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 05</div>
      <div class="plan-info">
        <div class="plan-title">Data Modeling</div>
        <div class="plan-sub">UsdGeomMesh · Primvars · Value types · TimeSamples</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 06</div>
      <div class="plan-info">
        <div class="plan-title">Visualization</div>
        <div class="plan-sub">UsdGeom · UsdShade · UsdLux · Material binding</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 07</div>
      <div class="plan-info">
        <div class="plan-title">Pipeline + Data Exchange</div>
        <div class="plan-sub">USDC vs USDA · Round-trip pipelines · Validators</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 08</div>
      <div class="plan-info">
        <div class="plan-title">Content Aggregation + Customising</div>
        <div class="plan-sub">Instancing · Custom schemas · AssetResolver</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 09</div>
      <div class="plan-info">
        <div class="plan-title">Debugging + Troubleshooting</div>
        <div class="plan-sub">usdview LayerStack · TfDebug · SdfChangeBlock</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
    <div class="plan-card">
      <div class="plan-day">DAY 10</div>
      <div class="plan-info">
        <div class="plan-title">Full Exam Simulation</div>
        <div class="plan-sub">All 13 sample questions · Timed · All domains</div>
      </div>
      <span class="plan-status status-soon">⏳ Soon</span>
    </div>
  </div>
</section>

<hr class="divider">

<!-- ══════════════ CODE SHOWCASE ══════════════ -->
<section class="code-section">
  <div class="code-inner">
    <div class="section-eyebrow">// Real code from the notes</div>
    <h2 class="section-title">Composition in Python</h2>
    <p class="section-desc">Every concept is backed by runnable code. Run it, open the .usda output in usdview, and see exactly how Python maps to USD scene description.</p>

    <div class="code-window">
      <div class="code-titlebar">
        <div class="dot dot-r"></div>
        <div class="dot dot-y"></div>
        <div class="dot dot-g"></div>
        <span class="code-filename">composition_demo.py</span>
      </div>
      <div class="code-body">
        <pre><code><span class="ck">from</span> <span class="cs">pxr</span> <span class="ck">import</span> <span class="cp">Usd</span>, <span class="cp">UsdGeom</span>, <span class="cp">Gf</span>

<span class="cm"># Create a stage — the composed view of your entire scene</span>
stage = <span class="cp">Usd</span>.<span class="cp">Stage</span>.<span class="cw">CreateNew</span>(<span class="cs">"scene.usda"</span>)
<span class="cp">UsdGeom</span>.<span class="cw">SetStageUpAxis</span>(stage, <span class="cp">UsdGeom</span>.<span class="cp">Tokens</span>.y)
stage.<span class="cw">SetMetadata</span>(<span class="cs">"metersPerUnit"</span>, <span class="cn">0.01</span>)

<span class="cm"># Reference a chair asset — graft it into this scene at /World/Chair</span>
chair = stage.<span class="cw">DefinePrim</span>(<span class="cs">"/World/Chair"</span>)
chair.<span class="cw">GetReferences</span>().<span class="cw">AddReference</span>(<span class="cs">"./chair.usda"</span>)

<span class="cm"># Local opinion overrides the referenced position — L beats R in LIVERPS</span>
<span class="cp">UsdGeom</span>.<span class="cp">XformCommonAPI</span>(chair).<span class="cw">SetTranslate</span>(<span class="cp">Gf</span>.<span class="cv">Vec3d</span>(<span class="cn">3</span>, <span class="cn">0</span>, <span class="cn">0</span>))

<span class="cm"># Variant sets — switchable options without duplicating the asset</span>
prim = stage.<span class="cw">GetPrimAtPath</span>(<span class="cs">"/World/Chair"</span>)
vset = prim.<span class="cw">GetVariantSets</span>().<span class="cw">AddVariantSet</span>(<span class="cs">"color"</span>)
vset.<span class="cw">SetVariantSelection</span>(<span class="cs">"blue"</span>)  <span class="cm"># override the default selection</span>

stage.<span class="cw">Save</span>()
<span class="ck">print</span>(stage.<span class="cw">ExportToString</span>(addSourceFileComment=<span class="cn">False</span>))</code></pre>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<!-- ══════════════ EXAM DOMAINS ══════════════ -->
<section class="domains-section">
  <div class="section-eyebrow">// Exam coverage</div>
  <h2 class="section-title">All 8 Exam Domains</h2>
  <p class="section-desc">The NCP OpenUSD Development exam covers 8 domains. Every domain is covered with dedicated notes, code examples, and practice questions.</p>

  <div class="domains-grid">
    <div class="domain-card">
      <div class="domain-icon">🧩</div>
      <div class="domain-name">Composition</div>
      <div class="domain-weight" style="color:var(--nvidia)">23% — highest weight</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">🔄</div>
      <div class="domain-name">Data Exchange</div>
      <div class="domain-weight">15%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">🏗️</div>
      <div class="domain-name">Pipeline Dev</div>
      <div class="domain-weight">14%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">📐</div>
      <div class="domain-name">Data Modeling</div>
      <div class="domain-weight">13%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">🐛</div>
      <div class="domain-name">Debugging</div>
      <div class="domain-weight">11%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">📦</div>
      <div class="domain-name">Content Agg.</div>
      <div class="domain-weight">10%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">🎨</div>
      <div class="domain-name">Visualization</div>
      <div class="domain-weight">8%</div>
    </div>
    <div class="domain-card">
      <div class="domain-icon">🔧</div>
      <div class="domain-name">Customising USD</div>
      <div class="domain-weight">6%</div>
    </div>
  </div>
</section>

<hr class="divider">

<!-- ══════════════ SETUP ══════════════ -->
<section class="setup-section">
  <div class="setup-inner">
    <div class="section-eyebrow">// Getting started</div>
    <h2 class="section-title">Run the Code Yourself</h2>
    <p class="section-desc" style="margin-bottom:1rem;">All Python examples are tested and runnable. You need usdview + usd-core installed. Follow these steps and you'll be up in under 5 minutes.</p>

    <div class="setup-steps">
      <div class="setup-step">
        <div class="step-num">1</div>
        <div class="step-body">
          <div class="step-title">Download OpenUSD libraries from NVIDIA's developer page and rename the folder to <code style="font-size:12px;color:var(--nvidia)">usd_root/</code></div>
        </div>
      </div>
      <div class="setup-step">
        <div class="step-num">2</div>
        <div class="step-body">
          <div class="step-title">Create and activate a Python virtual environment</div>
          <div class="step-cmd">python -m venv python-usd-venv &amp;&amp; python-usd-venv\Scripts\Activate.ps1</div>
        </div>
      </div>
      <div class="setup-step">
        <div class="step-num">3</div>
        <div class="step-body">
          <div class="step-title">Install usd-core</div>
          <div class="step-cmd">pip install usd-core</div>
        </div>
      </div>
      <div class="setup-step">
        <div class="step-num">4</div>
        <div class="step-body">
          <div class="step-title">Verify it works</div>
          <div class="step-cmd">python -c "from pxr import Usd; print(Usd.GetVersion())"</div>
        </div>
      </div>
      <div class="setup-step">
        <div class="step-num">5</div>
        <div class="step-body">
          <div class="step-title">Run any example and open the output in usdview</div>
          <div class="step-cmd">python code-examples/day1/hello_world.py &amp;&amp; .\scripts\usdview.bat hello_world.usda</div>
        </div>
      </div>
    </div>
  </div>
</section>


<!-- ══════════════ FOOTER ══════════════ -->
<footer class="footer">
  <div class="footer-glow"></div>
  <div class="footer-title">Open<span style="color:var(--teal)">USD</span> · Study Hard · Ship Scenes</div>
  <div class="footer-sub">Built with curiosity, NVIDIA's Learn OpenUSD docs, and a lot of usdview sessions.</div>
  <div class="footer-tags">
    <span class="tag green">OpenUSD</span>
    <span class="tag green">NVIDIA Certified</span>
    <span class="tag teal">Python</span>
    <span class="tag teal">usdview</span>
    <span class="tag">3D Pipelines</span>
    <span class="tag">VFX</span>
    <span class="tag">Animation</span>
    <span class="tag">Scene Description</span>
    <span class="tag">Composition</span>
    <span class="tag">LIVERPS</span>
  </div>
</footer>

</body>
</html>
