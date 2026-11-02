/* Compare (compare.html?a=<slug>&b=<slug>): two brands or properties side by side. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const yr=new Date().getFullYear();
$("yr").textContent=yr;

S.load().then(D=>{
  const recs=[...D.orgs.values()].sort((a,b)=>b.n-a.n);
  const byName=new Map();recs.forEach(r=>{byName.set(r.e.name.toLowerCase(),r);(r.e.aliases||[]).forEach(a=>{if(!byName.has(a.toLowerCase()))byName.set(a.toLowerCase(),r)})});
  $("names").innerHTML=recs.slice(0,1500).map(r=>`<option value="${esc(r.e.name)}">`).join("");
  const q=S.qs();
  let A=D.orgs.get(q.get("a")||"adidas")||recs[0], B=D.orgs.get(q.get("b")||"nike")||recs[1];
  $("a").value=A.e.name;$("b").value=B.e.name;
  const pick=(el,set)=>{el.onchange=()=>{const r=byName.get(el.value.trim().toLowerCase());if(r){set(r);draw()}}};
  pick($("a"),r=>A=r);pick($("b"),r=>B=r);

  function col(r,other){
    const label=r.kind==="brand"?`Brand · ${r.cat}`:`${r.ptype}`;
    const sp=[...r.sports.entries()].sort((a,b)=>b[1]-a[1]).slice(0,6);
    const max=Math.max(1,...sp.map(x=>x[1]));
    const counts=new Map();r.deals.forEach(x=>(x.other||[]).forEach(o=>{if(o){const m=counts.get(o.slug)||{e:o,n:0};m.n++;counts.set(o.slug,m)}}));
    const top=[...counts.values()].sort((a,b)=>b.n-a.n).slice(0,8);
    const tiers=new Map();r.deals.forEach(x=>tiers.set(x.d.tier,(tiers.get(x.d.tier)||0)+1));
    return `<div><div class="hd2">${L.mark(r.e,{px:88})}<div><span class="lbl mute-l">${esc(label)}</span><h2 class="disp">${esc(r.e.name)}</h2></div></div>
    <div class="stats" style="margin-top:20px">${[[r.n,"deals"],[r.thisYr,`in ${yr}`],[r.partners.size,"partners"],[r.sports.size,"sports"]].map(([v,l])=>`<div class="stat"><b>${v}</b><span>${l}</span></div>`).join("")}</div>
    <h4>Sports</h4><div class="hb">${sp.map(([k,v])=>`<span class="lb">${esc(k)}</span><span class="tr"><span class="br" style="width:${(v/max*100).toFixed(1)}%"></span></span><span class="vl">${v}</span>`).join("")}</div>
    <h4>Deal types</h4><div class="hb">${[...tiers.entries()].sort((a,b)=>b[1]-a[1]).slice(0,5).map(([k,v])=>`<span class="lb">${esc(k||"Other")}</span><span class="tr"><span class="br" style="width:${(v/r.n*100).toFixed(1)}%"></span></span><span class="vl">${v}</span>`).join("")}</div>
    <h4>Top partners</h4><ul>${top.map(m=>`<li><a class="lga" href="${esc(L.page(m.e.slug))}">${L.mark(m.e,{px:32})}</a><a href="${esc(L.page(m.e.slug))}">${esc(m.e.name)}</a><span class="d">${m.n} deal${m.n===1?"":"s"}</span></li>`).join("")}</ul>
    <h4>Latest deals</h4><ul>${r.deals.slice(0,6).map(x=>`<li>${S.dealLink(x.d)}<span class="d">${esc(S.fmt(x.d))}</span></li>`).join("")}</ul>
    <p style="margin-top:20px"><a class="more" href="${esc(L.page(r.e.slug))}">Full record →</a></p></div>`;
  }
  function draw(){
    const shared=[...A.partners.keys()].filter(k=>B.partners.has(k)).map(k=>A.partners.get(k));
    const sharedSports=[...A.sports.keys()].filter(k=>B.sports.has(k));
    const direct=A.deals.filter(x=>(x.other||[]).some(o=>o&&o.slug===B.e.slug));
    $("cmp").innerHTML=`<div class="shared" style="margin-top:32px"><span class="lbl mute-l">In common</span>
      <p style="margin:10px 0 0;font-size:17px;line-height:1.5">${direct.length?`<b>They've done ${direct.length} deal${direct.length===1?"":"s"} together.</b> `:""}${shared.length?`Both have signed with <b>${shared.slice(0,8).map(e=>esc(e.name)).join(", ")}</b>${shared.length>8?` and ${shared.length-8} more`:""}.`:"No shared partners filed."} ${sharedSports.length?`Both are in ${esc(sharedSports.join(", "))}.`:""}</p></div>
      <div class="cmp">${col(A,B)}${col(B,A)}</div>`;
    S.setQs({a:A.e.slug,b:B.e.slug});
  }
  draw();
}).catch(()=>{$("cmp").innerHTML=`<p class="note">Couldn't load. Refresh to try again.</p>`});
})();
