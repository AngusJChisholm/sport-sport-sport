/* Categories (categories.html): every brand category, and one category in detail with ?c=<name>. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const yr=new Date().getFullYear();
$("yr").textContent=yr;
const plural=(n,a,b)=>`${n.toLocaleString("en-AU")} ${n===1?a:b}`;

S.load().then(D=>{
  const q=S.qs(); const c=q.get("c");
  const byCat=new Map(S.CATS.map(k=>[k,{brands:[],deals:new Set()}]));
  D.brands.forEach(b=>{const g=byCat.get(b.cat)||byCat.get("Other");g.brands.push(b);b.deals.forEach(x=>{if(x.side==="b")g.deals.add(x.d)})});
  if(!c||!byCat.has(c))return index(byCat);
  detail(c,byCat.get(c),q);
}).catch(()=>{$("view").innerHTML=`<p class="wrap note">Couldn't load categories. Refresh to try again.</p>`});

function index(byCat){
  document.title="Categories | Sport Sport Sport";
  const cards=[...byCat.entries()].filter(([,g])=>g.brands.length).map(([k,g])=>{
    const top=[...g.brands].sort((a,b)=>b.n-a.n).slice(0,4);
    const ty=[...g.deals].filter(d=>S.yearOf(d)===yr).length;
    return {k,g,top,ty};
  }).sort((a,b)=>(a.k==="Other")-(b.k==="Other")||b.g.deals.size-a.g.deals.size);
  $("view").innerHTML=`<section class="wrap hero"><span class="lbl mute-l">Insights</span><h1 class="disp">Categories.</h1>
  <p>Every brand in the archive sorted into the industry it sells in. Pick one to see who's spending, which sports they back and every deal they've done.</p></section>
  <section class="wrap sec"><div class="cg">${cards.map(x=>`<a class="cc" href="categories.html?c=${encodeURIComponent(x.k)}"><h3>${esc(x.k)}</h3><span class="k">${plural(x.g.brands.length,"brand","brands")} · ${plural(x.g.deals.size,"deal","deals")}${x.ty?` · ${x.ty} in ${yr}`:""}</span><span class="lgs">${x.top.map(b=>L.mark(b.e,{px:40})).join("")}</span></a>`).join("")}</div></section>`;
}

function detail(c,g,q){
  document.title=`${c} sponsors | Sport Sport Sport`;
  const st={sport:q.get("sport")||"All",region:q.get("region")||"All"};
  const deals=[...g.deals].sort((a,b)=>S.sortKey(b).localeCompare(S.sortKey(a)));
  const sports=(()=>{const m=new Map();deals.forEach(d=>m.set(d.sport,(m.get(d.sport)||0)+1));return [...m.entries()].sort((a,b)=>b[1]-a[1]).map(x=>x[0])})();
  $("view").innerHTML=`<section class="wrap hero"><nav class="crumbs" style="padding:0 0 18px" aria-label="Breadcrumb"><a href="insights.html">Insights</a><span aria-hidden="true">/</span><a href="categories.html">Categories</a></nav>
  <span class="lbl mute-l">Category</span><h1 class="disp" style="font-size:clamp(48px,8vw,128px)">${esc(c)}.</h1><div class="stats" id="cStats" style="margin-top:32px"></div></section>
  <section class="wrap" style="padding-top:28px"><div class="ctl2"><div class="pills" id="spPills" role="group" aria-label="Sport"></div><div class="pills" id="regPills" role="group" aria-label="Region"></div></div></section>
  <section class="wrap sec" style="padding-top:12px"><div class="sh"><div><span class="lbl mute-l">The spenders</span><h2 class="disp">Brands.</h2></div><span class="lbl mute-l" id="bCount"></span></div><div class="dg" id="bGrid"></div></section>
  <section class="wrap sec" style="padding-top:0"><div class="sh"><div><span class="lbl mute-l">Who they back</span><h2 class="disp">Properties.</h2></div><span class="lbl mute-l" id="pCount"></span></div><div class="pg" id="pGrid"></div></section>
  <section class="wrap sec" style="padding-top:0"><div class="sh"><div><span class="lbl mute-l">The record</span><h2 class="disp">Every deal.</h2></div><span class="lbl mute-l" id="dCount"></span></div><div class="tw"><table class="t"><thead><tr><th>Date</th><th>Deal</th><th>Sport</th><th>Deal type</th><th>Ends</th><th>Region</th></tr></thead><tbody id="dRows"></tbody></table></div></section>`;
  function draw(){
    const r=deals.filter(d=>(st.sport==="All"||d.sport===st.sport)&&(st.region==="All"||d.region===st.region));
    const bm=new Map(),pm=new Map();
    r.forEach(d=>{d._bs.forEach(e=>{if(e&&g.brands.some(b=>b.e.slug===e.slug)){const m=bm.get(e.slug)||{e,n:0,sp:new Set()};m.n++;m.sp.add(d.sport);bm.set(e.slug,m)}});
      d._ps.forEach(e=>{if(!e)return;const m=pm.get(e.slug)||{e,n:0,sp:new Set()};m.n++;m.sp.add(d.sport);pm.set(e.slug,m)})});
    const bs=[...bm.values()].sort((a,b)=>b.n-a.n||a.e.name.localeCompare(b.e.name));
    const ps=[...pm.values()].sort((a,b)=>b.n-a.n||a.e.name.localeCompare(b.e.name));
    $("cStats").innerHTML=[[bs.length,"brands"],[r.length,"deals"],[r.filter(d=>S.yearOf(d)===yr).length,`in ${yr}`],[ps.length,"properties backed"]].map(([v,l])=>`<div class="stat"><b>${v.toLocaleString("en-AU")}</b><span>${l}</span></div>`).join("");
    $("bCount").textContent=plural(bs.length,"brand","brands");
    $("bGrid").innerHTML=bs.map(m=>`<a class="dt" href="${esc(L.page(m.e.slug))}">${L.mark(m.e,{px:72})}<b>${esc(m.e.name)}</b><span class="n">${m.n} deal${m.n===1?"":"s"}</span><span class="k">${esc([...m.sp].slice(0,2).join(" · "))}</span></a>`).join("")||`<p class="note">No deals for that filter.</p>`;
    $("pCount").textContent=plural(ps.length,"property","properties");
    $("pGrid").innerHTML=ps.slice(0,48).map(m=>`<a class="pt" href="${esc(L.page(m.e.slug))}">${L.mark(m.e,{px:64})}<b>${esc(m.e.name)}</b><span class="k">${m.n>1?m.n+" deals · ":""}${esc([...m.sp].join(", "))}</span></a>`).join("");
    $("dCount").textContent=plural(r.length,"deal","deals");
    $("dRows").innerHTML=r.map(d=>`<tr><td class="d">${esc(S.fmt(d))}</td><td><span class="dl">${L.pair(d,{px:34})}${S.dealLink(d)}</span></td><td>${esc(d.sport)}</td><td>${esc(d.tier||d.type||"")}</td><td class="d">${esc(S.endsTxt(d))}</td><td><span class="tag r">${esc(d.region)}</span></td></tr>`).join("");
    $("spPills").innerHTML=["All",...sports.slice(0,14)].map(s=>`<button type="button" class="pill${st.sport===s?" on":""}" data-s="${esc(s)}" aria-pressed="${st.sport===s}">${s==="All"?"All sports":esc(s)}</button>`).join("");
    $("regPills").innerHTML=["All","ANZ","Global"].map(x=>`<button type="button" class="pill${st.region===x?" on":""}" data-r="${x}" aria-pressed="${st.region===x}">${x==="All"?"Everywhere":x}</button>`).join("");
    S.setQs({c,sport:st.sport!=="All"&&st.sport,region:st.region!=="All"&&st.region});
  }
  $("view").addEventListener("click",e=>{const b=e.target.closest("[data-s],[data-r]");if(!b)return;if(b.dataset.s)st.sport=b.dataset.s;if(b.dataset.r)st.region=b.dataset.r;draw()});
  draw();
}
})();
