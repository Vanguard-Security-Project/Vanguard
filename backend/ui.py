#the dashboard

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vanguard</title>
<style>
:root{--bg:#0f1216;--panel:#161b22;--panel2:#1c232c;--border:#2a323d;
--fg:#e6edf3;--muted:#8b98a5;--accent:#4ea1ff;--high:#ff6b6b;
--review:#f0b429;--ok:#4ade80}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
header{border-bottom:1px solid var(--border);padding:14px 20px;
display:flex;gap:12px;align-items:center;flex-wrap:wrap;background:#141a22;
position:sticky;top:0;z-index:5}
header h1{margin:0;font-size:18px}
.badge{padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;
text-transform:uppercase;letter-spacing:.5px;border:1px solid var(--border);
color:var(--muted)}
.badge.running{color:#7cc4ff;border-color:#2f5480;background:#0f1c2c}
.badge.done{color:var(--ok);border-color:#155e3b;background:#0f2419}
.badge.error{color:var(--high);border-color:#7a2b2b;background:#2a1414}
main{padding:20px;max-width:1100px;margin:0 auto}
section{margin-bottom:20px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.6px;
color:var(--muted);margin:0 0 10px}
.panel{background:var(--panel);border:1px solid var(--border);
border-radius:10px;padding:16px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
gap:10px}
.card{background:var(--panel2);border:1px solid var(--border);
border-radius:8px;padding:14px;text-align:center}
.card .n{font-size:24px;font-weight:700;color:var(--accent)}
.card .l{color:var(--muted);font-size:11px;text-transform:uppercase;
letter-spacing:.5px;margin-top:4px}
.card.high .n{color:var(--high)}
.card.ok .n{color:var(--ok)}
input[type=file]{color:var(--fg);background:var(--panel2);
border:1px dashed var(--border);padding:8px;border-radius:7px;flex:1;
min-width:180px;font:inherit}
button{background:var(--accent);color:#fff;border:0;padding:8px 14px;
border-radius:8px;cursor:pointer;font-weight:600;font-size:13px;
font-family:inherit}
button:hover{filter:brightness(1.1)}
button:disabled{opacity:.5;cursor:not-allowed}
.muted{color:var(--muted);font-size:12px}
.flash{padding:10px 14px;border-radius:8px;margin-bottom:12px;
border:1px solid var(--border);background:var(--panel2);font-size:13px}
.flash.success{border-color:#155e3b;background:#0f2419;color:#bff5d4}
.flash.error{border-color:#7a2b2b;background:#2a1414;color:#ffd4d4}
.stage{border:1px solid var(--border);border-radius:10px;padding:14px;
margin-bottom:10px;background:var(--panel);border-left:4px solid var(--ok)}
.stage .head{display:flex;justify-content:space-between;align-items:center;
gap:10px;flex-wrap:wrap;margin-bottom:8px}
.stage .head b{font-size:14px}
.stage .head .st{font-size:11px;color:var(--muted);text-transform:uppercase;
letter-spacing:.5px}
.finding{border:1px solid var(--border);border-radius:8px;padding:10px;
margin-bottom:6px;background:var(--panel)}
.finding.High{border-left:4px solid var(--high)}
.finding.Review{border-left:4px solid var(--review)}
.finding.Low{border-left:4px solid var(--muted)}
.path{font-family:ui-monospace,Consolas,monospace;font-size:12px;
margin:5px 0;word-break:break-word}
.rel{font-size:11px;color:var(--muted);margin-top:4px}
.rel code{background:#0d1117;padding:1px 5px;border-radius:4px;
color:#ffb86c;border:1px solid var(--border)}
.arrow{color:var(--muted);margin:0 6px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{padding:7px 9px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:11px;
letter-spacing:.5px}
td.ok{color:var(--ok)}td.bad{color:var(--high)}
code{background:#0d1117;padding:1px 5px;border-radius:4px;color:#ffb86c;
border:1px solid var(--border);font-size:12px}
footer{text-align:center;color:var(--muted);font-size:11.5px;padding:18px;
border-top:1px solid var(--border);margin-top:30px}
</style>
</head>
<body>
<header>
  <h1>Vanguard</h1>
  <span class="badge" id="status">idle</span>
  <span class="muted" style="margin-left:auto">
    scan &rarr; analyze &rarr; fix &rarr; re-attack &rarr; verify
  </span>
</header>
<main>
  <div id="flash"></div>

  <section>
    <h2>Stage 1 &mdash; Upload a real export</h2>
    <div class="panel">
      <p class="muted" style="margin:0 0 10px">
        Requires a SharpHound or BloodHound collection (.zip or .json).
        No synthetic data is accepted or generated.
      </p>
      <div class="row">
        <input type="file" id="fileInput" accept=".json,.zip">
        <button id="runBtn">Run pipeline</button>
      </div>
      <details style="margin-top:12px">
        <summary class="muted">Optional: real re-attack credentials</summary>
        <p class="muted" style="margin:6px 0">
          Leave blank to use graph verification. Provide credentials to run
          the actual technique against the target (lab only).
        </p>
        <input type="text" id="credsJson" style="width:100%;padding:8px;
          background:#1c232c;border:1px solid #2a323d;border-radius:7px;
          color:#e6edf3;font-family:ui-monospace,Consolas,monospace"
          placeholder='{"technique":"dcsync","target":"dc01.lab.local","user":"svc.sql","domain":"LAB","secret":"..."}'>
      </details>
    </div>
  </section>

  <section id="result" hidden></section>
</main>
<footer>
  Vanguard &middot; operates on real exports only &middot; no AD changes are made by this app
</footer>
<script>
(function(){
"use strict";
var $ = function(id){return document.getElementById(id);};
function setStatus(t,k){var e=$("status");e.textContent=t;
  e.className="badge"+(k?" "+k:"");}
function flash(m,k){var b=$("flash");if(!m){b.innerHTML="";return;}
  b.innerHTML='<div class="flash '+(k||'')+'">'+escapeHtml(m)+'</div>';}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function shortName(id){if(!id)return "?";var s=String(id);
  return (s.length>20&&s.indexOf("-")>=0)?s.split("-").pop():s;}

function api(path,opts){
  return fetch(path,opts).then(function(res){
    return res.text().then(function(text){
      var data;
      try{data=text?JSON.parse(text):{};}catch(e){data={raw:text};}
      if(!res.ok){throw new Error(data.detail||data.error||data.raw||("HTTP "+res.status));}
      return data;
    });
  });
}

function render(r){
  $("result").hidden=false;
  var a=r.analysis;
  var beforeSucceeded=(r.reattack_before||[]).filter(function(b){
    return b.graph_check&&b.graph_check.succeeded;}).length;

  var cards=[
    ["Nodes",a.node_count,""],
    ["Edges",a.edge_count,""],
    ["Findings",a.path_count,""],
    ["High risk",a.high_count,"high"],
    ["Paths before",beforeSucceeded,""],
    ["Verified fixed",r.verification_summary.verified_fixed,"ok"],
  ];
  var cardsHtml=cards.map(function(c){
    return '<div class="card '+c[2]+'"><div class="n">'+c[1]+
      '</div><div class="l">'+c[0]+'</div></div>';}).join("");

  var findingsHtml=(a.findings||[]).slice(0,10).map(function(f){
    var nodes=(f.nodes||[]).map(function(n){
      return escapeHtml(shortName(n.name||n.id));}).join('<span class="arrow">\u2192</span>');
    var rels=(f.edges||[]).map(function(e){
      return '<code>'+escapeHtml(e.relationship)+'</code>';}).join(" \u00b7 ");
    return '<div class="finding '+f.risk+'">'+
      '<div style="display:flex;justify-content:space-between;align-items:baseline;'+
      'gap:10px;flex-wrap:wrap"><div><b>'+escapeHtml(shortName(f.start_name))+'</b>'+
      '<span class="arrow">\u2192</span><b>'+escapeHtml(shortName(f.target_name))+'</b>'+
      '<span class="muted"> \u00b7 score '+f.score+' \u00b7 '+f.hops+' hops</span></div>'+
      '<span class="badge'+(f.risk==='High'?' error':'')+'">'+escapeHtml(f.risk)+'</span>'+
      '</div><div class="path">'+nodes+'</div><div class="rel">'+rels+'</div></div>';
  }).join("") || '<p class="muted">No paths found in this export. '+
    'Verify collection scope before concluding the environment is safe.</p>';

  var decisionsHtml=(r.fix.decisions||[]).map(function(d){
    return '<tr><td>'+escapeHtml(shortName(d.start))+'</td><td>'+
      escapeHtml(shortName(d.target))+'</td><td><code>'+
      escapeHtml(d.kind||"none")+'</code></td><td>'+
      escapeHtml(d.blast_radius||"\u2014")+'</td></tr>';}).join("");

  var verifyHtml=(r.verify_after||[]).map(function(v){
    var s=v.graph_check&&v.graph_check.succeeded;
    return '<tr><td>'+escapeHtml(shortName(v.finding.start_name))+'</td><td>'+
      escapeHtml(shortName(v.finding.target_name))+'</td><td class="'+
      (s?'bad':'ok')+'">'+(s?'present':'absent')+'</td><td class="'+
      (v.verdict==='verified_fixed'?'ok':'bad')+'">'+escapeHtml(v.verdict)+
      '</td></tr>';}).join("");

  $("result").innerHTML=
    '<section><h2>Summary</h2><div class="grid">'+cardsHtml+'</div></section>'+
    '<section><h2>Stage 1 &mdash; Scan</h2>'+
    '<div class="stage"><div class="head"><b>'+escapeHtml(r.source.filename)+
    '</b><span class="st">'+r.source.nodes+' nodes / '+r.source.edges+
    ' edges</span></div><p class="muted">Neo4j: '+
    escapeHtml(JSON.stringify(r.source.persist))+'</p></div></section>'+
    '<section><h2>Stage 2 &mdash; Analyze</h2>'+
    '<div class="stage"><div class="head"><b>'+a.path_count+
    ' path(s) to Tier-0</b><span class="st">'+a.high_count+' high \u00b7 '+
    a.review_count+' review</span></div>'+findingsHtml+'</div></section>'+
    '<section><h2>Stage 3+4 &mdash; Fix plan</h2>'+
    '<div class="stage"><div class="head"><b>'+r.fix.action_count+
    ' fix(es) proposed</b><span class="st">least-disruptive rule match</span>'+
    '</div><table><thead><tr><th>Start</th><th>Target</th><th>Fix</th>'+
    '<th>Blast</th></tr></thead><tbody>'+
    (decisionsHtml||'<tr><td colspan="4" class="muted">no decisions</td></tr>')+
    '</tbody></table><p class="muted" style="margin-top:10px">Apply: <code>'+
    escapeHtml(r.fix.apply_script)+'</code><br>Rollback: <code>'+
    escapeHtml(r.fix.rollback_script)+'</code></p></div></section>'+
    '<section><h2>Stage 4 &mdash; Re-attack (before)</h2>'+
    '<div class="stage"><div class="head"><b>'+beforeSucceeded+' of '+
    (r.reattack_before||[]).length+' paths present</b>'+
    '<span class="st">graph verification</span></div></div></section>'+
    '<section><h2>Stage 5 &mdash; Verify (after)</h2>'+
    '<div class="stage"><div class="head"><b>'+
    r.verification_summary.verified_fixed+' of '+
    r.verification_summary.findings_tested+' paths removed</b>'+
    '<span class="st">graph diff</span></div><table><thead><tr><th>Start</th>'+
    '<th>Target</th><th>Path</th><th>Verdict</th></tr></thead><tbody>'+
    (verifyHtml||'<tr><td colspan="4" class="muted">no findings tested</td></tr>')+
    '</tbody></table></div></section>'+
    '<section><h2>Re-analysis</h2><div class="stage"><div class="head"><b>'+
    r.reanalysis.path_count+' path(s) remain</b><span class="st">was '+
    a.path_count+' before</span></div></div></section>';
}

function run(){
  var f=$("fileInput").files[0];
  if(!f){flash("Choose a SharpHound or BloodHound export first.","error");return;}
  setStatus("running","running");flash("");
  var fd=new FormData();
  fd.append("file",f);
  var c=$("credsJson").value.trim();
  if(c) fd.append("creds_json",c);
  api("/api/pipeline/run",{method:"POST",body:fd}).then(function(r){
    render(r);setStatus("done","done");
    flash("Pipeline complete: "+r.analysis.path_count+" findings, "+
          r.verification_summary.verified_fixed+" verified fixed.","success");
  }).catch(function(e){setStatus("error","error");flash("Error: "+e.message,"error");});
}

$("runBtn").addEventListener("click",run);
fetch("/api/health").catch(function(){setStatus("offline","error");});
})();
</script>
</body>
</html>
"""
