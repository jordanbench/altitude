# Tab template

Start every altitude page from this skeleton. It gives you:

- Four tabs in a fixed order, opening on the 10k view.
- An intro line at the top of each tab that states its question and when to read it.
- Keyboard support: the arrow keys move between tabs.
- Deep links: `#v10k`, `#v5k`, `#v1k`, and `#v100` open a tab directly.
- Light and dark themes through color tokens.
- A layout that works at phone width.

Replace the colors, fonts, and content to fit the subject. Keep the tab structure, the order, and the 10k default.

```html
<title>Topic name</title>
<style>
:root{--bg:#f4f6f8;--surface:#fff;--ink:#16202b;--muted:#5a6675;--line:#dbe1e7;--accent:#0b6e8a;--accent-soft:#dcedf2}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#10161c;--surface:#171f27;--ink:#e5eaf0;--muted:#95a2b0;--line:#29333e;--accent:#5cc2de;--accent-soft:#16303a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#10161c;--surface:#171f27;--ink:#e5eaf0;--muted:#95a2b0;--line:#29333e;--accent:#5cc2de;--accent-soft:#16303a;color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding-inline:16px;padding-block:28px 64px}
.tabs{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);display:flex;gap:8px;flex-wrap:wrap;padding-block:10px;border-bottom:1px solid var(--line)}
.tabs button{font:500 13px/1 ui-monospace,monospace;padding:8px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--muted);cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.panel{display:flex;flex-direction:column;gap:20px;padding-top:24px}
.fig{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px}
.fig svg{display:block;width:100%;height:auto}
.tbl{overflow-x:auto}
.where{margin:0;padding:10px 14px;border-left:3px solid var(--accent);background:var(--accent-soft);border-radius:0 8px 8px 0;font-size:15px}
/* 10k view: one idea per pane, a big picture, a few words */
.pane{background:var(--surface);border-radius:18px;padding:26px;display:grid;gap:16px}
.pane h2{margin:0;font-size:clamp(28px,5vw,44px);line-height:1.05;text-wrap:balance}
.pane p{margin:0;font-size:19px;line-height:1.45;max-width:50ch}
.pane .pic{background:var(--bg);border-radius:12px;padding:12px}
.pane svg{display:block;width:100%;height:auto}
.pane .two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.lb{font-weight:700;font-size:22px;fill:var(--ink)}
.lb.s{font-size:16px;fill:var(--muted)}
.lb.h{font-size:40px}
@media (max-width:640px){.pane{padding:18px}.pane .two{grid-template-columns:1fr}}
</style>

<div class="wrap">
  <h1>Topic name</h1>
  <div class="tabs" role="tablist" aria-label="Altitude">
    <button role="tab" id="t-v10k" aria-controls="v10k" aria-selected="true">10k view</button>
    <button role="tab" id="t-v5k" aria-controls="v5k" aria-selected="false">5k view</button>
    <button role="tab" id="t-v1k" aria-controls="v1k" aria-selected="false">1k view</button>
    <button role="tab" id="t-v100" aria-controls="v100" aria-selected="false">100 view</button>
  </div>
  <section class="panel" role="tabpanel" id="v10k" aria-labelledby="t-v10k">
    <p class="where"><b>What is it?</b> Start here. What this is, in pictures.</p>
    <!-- One pane per idea. Repeat 5 to 10 times. -->
    <div class="pane">
      <h2>Same slots. New order. That's it.</h2>
      <div class="pic">
        <svg viewBox="0 0 960 300" role="img" aria-label="Describe the picture in one sentence">
          <!-- Draw real things from the topic: a van, a calendar, a switch, a receipt. -->
          <!-- Labels: <text class="lb">big label</text>, <text class="lb s">small label</text> -->
        </svg>
      </div>
      <p>One line, or nothing.</p>
    </div>
  </section>
  <section class="panel" role="tabpanel" id="v5k" aria-labelledby="t-v5k" hidden>
    <p class="where"><b>How does it work?</b> Read this if the 10k view made sense and you want the moving parts.</p>
    <!-- Parts diagram and data flow. Pick up where the 10k view left off. -->
  </section>
  <section class="panel" role="tabpanel" id="v1k" aria-labelledby="t-v1k" hidden>
    <p class="where"><b>What should we decide?</b> Read this if you need to make a call. The risks, trade-offs, and what I'd do.</p>
    <!-- Decision tables, edge cases, the recommendation, and the plan. Don't re-explain how it works. -->
  </section>
  <section class="panel" role="tabpanel" id="v100" aria-labelledby="t-v100" hidden>
    <p class="where"><b>Prove it.</b> Read this to check any claim above. The evidence behind each one.</p>
    <!-- Evidence tied to each claim: code, queries and results, PR links, commands. -->
  </section>
</div>

<script>
(function(){
  var tabs=[].slice.call(document.querySelectorAll('[role="tab"]'));
  function show(id){tabs.forEach(function(t){var on=t.getAttribute('aria-controls')===id;t.setAttribute('aria-selected',on);t.tabIndex=on?0:-1;document.getElementById(t.getAttribute('aria-controls')).hidden=!on;});}
  tabs.forEach(function(t,i){
    t.addEventListener('click',function(){show(t.getAttribute('aria-controls'));try{history.replaceState(null,'','#'+t.getAttribute('aria-controls'))}catch(e){}});
    t.addEventListener('keydown',function(e){var d=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;if(!d)return;var n=tabs[(i+d+tabs.length)%tabs.length];n.focus();n.click();});
  });
  var h=(location.hash||'').slice(1);
  show(/^v(10k|5k|1k|100)$/.test(h)?h:'v10k');
})();
</script>
```

## Visuals

- Draw diagrams as inline SVG, and color them with the page's tokens so they work in both themes.
- Wrap each diagram in `.fig`. Wrap each wide table in `.tbl` so it scrolls inside its own box.
- Label every box and arrow with words the reader would use.
- Draw charts to scale, and only from real numbers you looked up. Never invent data to fill a chart.
