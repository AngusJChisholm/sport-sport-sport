/* SSS Pro (pro.html): private working tool built on the deal archive.
   Tabs: Matches (Match Score suggestions, both ways), Brand finder, Renewal radar, Property report (partners, category gaps, prospects, peer benchmark), Watchlist.
   Renewal years come in three strengths:
     Confirmed  - the announcement states when the deal ends
     From term  - the announcement states the length; end year = announced year + term
     Estimate   - neither is stated; end year = announced year + the typical term for that deal type,
                  worked out from every deal in the archive that does state a term */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const NOW=new Date(), yr=NOW.getFullYear();
$("yr").textContent=yr;

/* ---------- small helpers ---------- */
const WKEY="sssPro.watch";
const watch={get(){try{return new Set(JSON.parse(localStorage.getItem(WKEY)||"[]"))}catch(e){return new Set()}},
  toggle(slug){const s=this.get();s.has(slug)?s.delete(slug):s.add(slug);try{localStorage.setItem(WKEY,JSON.stringify([...s]))}catch(e){}return s.has(slug)}};
const star=slug=>`<button type="button" class="star${watch.get().has(slug)?" on":""}" data-star="${esc(slug)}" aria-label="Watch" title="Add to watchlist">${watch.get().has(slug)?"★":"☆"}</button>`;
const dated=d=>!!(d.date||d.month);
const yearOf=d=>dated(d)?S.yearOf(d):0;
const monthsAgo=d=>{if(!dated(d))return 999;const k=S.sortKey(d);const y=+k.slice(0,4),m=+k.slice(5,7)||1;return (NOW.getFullYear()-y)*12+(NOW.getMonth()+1-m)};
const nameOf=d=>(d._bs||[]).map(e=>e.name).join(" / ");
const propOf=d=>(d._ps||[]).map(e=>e.name).join(" / ");
const logo=(e,px)=>e?L.link(e,{px:px||30}):"";
const opt=(v,cur,label)=>`<option value="${esc(v)}"${v===cur?" selected":""}>${esc(label||v)}</option>`;
const pills=(name,list,cur)=>list.map(([v,lab])=>`<button type="button" class="pill${cur===v?" on":""}" data-${name}="${esc(v)}" aria-pressed="${cur===v}">${esc(lab)}</button>`).join("");
function csv(rows,file){
  const q=v=>{v=v==null?"":String(v);return /[",\n]/.test(v)?`"${v.replace(/"/g,'""')}"`:v};
  const blob=new Blob(["﻿"+rows.map(r=>r.map(q).join(",")).join("\n")],{type:"text/csv"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=file;document.body.appendChild(a);a.click();a.remove();
}
// A deal is treated as live if its end year hasn't passed, or (with no end) it was announced in the last 3 years, or it's on the club's current partners page.
const live=d=>d.ends?d.ends>=yr:dated(d)?yearOf(d)>=yr-3:true;

let D,TYP={},TYP_ALL=3,state={tab:"dash"};

/* ---------- renewal year for a deal ---------- */
function renewal(d){
  if(d.ends)return {end:d.ends,basis:d.endsEst?"From term":"Confirmed"};
  if(!dated(d)||d.status==="Current partner")return null;
  const t=TYP[d.tier]||TYP_ALL;
  return {end:yearOf(d)+t,basis:"Estimate",t};
}
const basisTag=r=>r?`<span class="basis ${r.basis==="Confirmed"?"c":r.basis==="From term"?"t":""}" title="${r.basis==="Estimate"?`Typical ${r.t}-year term for this deal type`:r.basis==="From term"?"Announced term added to the announcement year":"End date stated in the announcement"}">${r.basis}</span>`:"";

/* ---------- Brand finder ---------- */
function finder(){
  const f=state.f||(state.f={q:"",cat:"",backs:"",notIn:"",region:"ANZ",win:"24",sort:"recent"});
  const sports=[...new Set(D.deals.map(d=>d.sport))].filter(Boolean).sort();
  $("view").innerHTML=`<p class="pro-intro">Brands spending in sport. Filter by category and the sports they back, or leave out a sport to find brands active elsewhere who haven't come into yours yet.</p>
  <div class="ctl"><input class="srch" id="fq" type="search" placeholder="Search a brand" value="${esc(f.q)}" autocomplete="off">
  <select class="sel" id="fcat"><option value="">All categories</option>${S.CATS.map(c=>opt(c,f.cat)).join("")}</select>
  <select class="sel" id="fbacks"><option value="">Backs any sport</option>${sports.map(s=>opt(s,f.backs,"Backs "+s)).join("")}</select>
  <select class="sel" id="fnot"><option value="">Not in: no exclusion</option>${sports.map(s=>opt(s,f.notIn,"Not in "+s)).join("")}</select></div>
  <div class="ctl2"><div class="pills">${pills("win",[["12","Active last 12 months"],["24","Last 2 years"],["36","Last 3 years"],["all","Any time"]],f.win)}</div>
  <div class="pills">${pills("reg",[["ANZ","ANZ deals"],["Global","Global deals"],["All","Everywhere"]],f.region)}${pills("sort",[["recent","Newest first"],["deals","Most deals"]],f.sort)}</div></div>
  <div class="res"><span class="lbl mute-l" id="fcount"></span><span class="toolrow"><button class="ghost" id="fcsv">Export CSV</button></span></div><div id="flist"></div>`;
  const draw=()=>{
    const q=f.q.trim().toLowerCase(), win=f.win==="all"?Infinity:+f.win;
    const rows=[];
    D.brands.forEach(b=>{
      if(q&&!b.hay.includes(q))return;
      if(f.cat&&b.cat!==f.cat)return;
      const ds=b.deals.filter(x=>f.region==="All"||x.d.region===f.region);
      if(!ds.length)return;
      if(f.backs&&!ds.some(x=>x.d.sport===f.backs))return;
      if(f.notIn&&b.deals.some(x=>x.d.sport===f.notIn))return;
      const recent=ds.filter(x=>monthsAgo(x.d)<=win);
      if(!recent.length)return;
      const last=ds.find(x=>dated(x.d))||ds[0];
      const sp=new Map();ds.forEach(x=>sp.set(x.d.sport,(sp.get(x.d.sport)||0)+1));
      const partners=[];const seen=new Set();ds.forEach(x=>(x.other||[]).forEach(o=>{if(o&&!seen.has(o.slug)&&partners.length<4){seen.add(o.slug);partners.push(o)}}));
      rows.push({b,n:ds.length,nRecent:recent.length,last:last.d,sports:[...sp.entries()].sort((a,c)=>c[1]-a[1]).map(x=>x[0]),partners});
    });
    rows.sort(f.sort==="deals"?(a,c)=>c.n-a.n||S.sortKey(c.last).localeCompare(S.sortKey(a.last)):(a,c)=>S.sortKey(c.last).localeCompare(S.sortKey(a.last))||c.n-a.n);
    state.fRows=rows;
    $("fcount").textContent=`${rows.length} brand${rows.length===1?"":"s"}`;
    const shown=rows.slice(0,state.fMore?rows.length:150);
    $("flist").innerHTML=rows.length?`<div class="tw"><table class="t"><thead><tr><th></th><th>Brand</th><th>Category</th><th>Deals</th><th>Last deal</th><th>Sports</th><th>Partners</th></tr></thead><tbody>${shown.map(r=>`<tr><td>${star(r.b.e.slug)}</td><td><span class="dl">${logo(r.b.e,34)}<a href="${esc(L.page(r.b.e.slug))}"><b>${esc(r.b.e.name)}</b></a></span></td><td>${esc(r.b.cat)}</td><td class="d">${r.n}${r.nRecent!==r.n?` <span class="mute-l">(${r.nRecent} recent)</span>`:""}</td><td class="d">${esc(S.fmt(r.last))}</td><td><div class="chips">${r.sports.slice(0,3).map(s=>`<span class="chip">${esc(s)}</span>`).join("")}</div></td><td><div class="logos">${r.partners.map(p=>logo(p,28)).join("")}</div></td></tr>`).join("")}</tbody></table></div>${rows.length>shown.length?`<p><button class="ghost" id="fmore">Show all ${rows.length}</button></p>`:""}`:`<p class="note">No brands match. Try a wider time window.</p>`;
  };
  let t;$("fq").oninput=e=>{clearTimeout(t);t=setTimeout(()=>{f.q=e.target.value;draw()},150)};
  $("fcat").onchange=e=>{f.cat=e.target.value;draw()};
  $("fbacks").onchange=e=>{f.backs=e.target.value;draw()};
  $("fnot").onchange=e=>{f.notIn=e.target.value;draw()};
  $("view").onclick=e=>{
    const b=e.target.closest("[data-win],[data-reg],[data-sort]");
    if(b){if(b.dataset.win)f.win=b.dataset.win;if(b.dataset.reg)f.region=b.dataset.reg;if(b.dataset.sort)f.sort=b.dataset.sort;
      b.parentNode.querySelectorAll(".pill").forEach(p=>{const on=p===b||(p.dataset.win&&p.dataset.win===f.win)||(p.dataset.reg&&p.dataset.reg===f.region)||(p.dataset.sort&&p.dataset.sort===f.sort);p.classList.toggle("on",!!on)});draw();return}
    if(e.target.id==="fmore"){state.fMore=true;draw();return}
    if(e.target.id==="fcsv")csv([["Brand","Category","Deals","Last deal","Sports","Recent partners"],...state.fRows.map(r=>[r.b.e.name,r.b.cat,r.n,S.fmt(r.last),r.sports.join("; "),r.partners.map(p=>p.name).join("; ")])],"sss-pro-brands.csv");
  };
  draw();
}

/* ---------- Renewal radar ---------- */
function renewals(){
  const def=String(NOW.getMonth()>=8?yr+1:yr);
  const f=state.r||(state.r={q:"",sport:"",cat:"",tier:"",region:"ANZ",year:def,basis:"all"});
  const all=D.deals.map(d=>({d,r:renewal(d)})).filter(x=>x.r&&x.r.end>=yr-2);
  const sports=[...new Set(all.map(x=>x.d.sport))].filter(Boolean).sort();
  const years=[["due","Due now"],[String(yr),String(yr)],[String(yr+1),String(yr+1)],[String(yr+2),String(yr+2)],["later",`${yr+3}+`]];
  const inYr=(x,y)=>y==="due"?x.r.end<yr&&x.r.basis==="Estimate":y==="later"?x.r.end>=yr+3:x.r.end===+y;
  $("view").innerHTML=`<p class="pro-intro">Deals reaching the end of their term. <b>Confirmed</b> means the end date was announced, and <b>From term</b> means the length was. <b>Estimate</b> adds the typical length for that deal type (${Object.entries(TYP).map(([k,v])=>`${k} ${v} yrs`).join(", ")}). <b>Due now</b> is estimates whose term has already run, so they're either renewed quietly or up for grabs.</p>
  <div class="ctl"><input class="srch" id="rq" type="search" placeholder="Search a brand or property" value="${esc(f.q)}" autocomplete="off">
  <select class="sel" id="rsport"><option value="">All sports</option>${sports.map(s=>opt(s,f.sport)).join("")}</select>
  <select class="sel" id="rcat"><option value="">All categories</option>${S.CATS.map(c=>opt(c,f.cat)).join("")}</select>
  <select class="sel" id="rtier"><option value="">All deal types</option>${S.TIERS.map(c=>opt(c,f.tier)).join("")}</select></div>
  <div class="ctl2"><div class="pills" id="ryears"></div><div class="pills">${pills("reg",[["ANZ","ANZ"],["Global","Global"],["All","Everywhere"]],f.region)}${pills("basis",[["all","Any basis"],["firm","Confirmed + From term"],["Confirmed","Confirmed only"]],f.basis)}</div></div>
  <div class="res"><span class="lbl mute-l" id="rcount"></span><button class="ghost" id="rcsv">Export CSV</button></div><div id="rlist"></div>`;
  const draw=()=>{
    const q=f.q.trim().toLowerCase();
    const base=all.filter(x=>(!q||x.d.deal.toLowerCase().includes(q))&&(!f.sport||x.d.sport===f.sport)&&(!f.cat||(x.d._cats||[]).includes(f.cat))&&(!f.tier||x.d.tier===f.tier)&&(f.region==="All"||x.d.region===f.region)
      &&(f.basis==="all"||(f.basis==="firm"?x.r.basis!=="Estimate":x.r.basis==="Confirmed"))
      );
    $("ryears").innerHTML=years.map(([v,lab])=>{const n=base.filter(x=>inYr(x,v)).length;return `<button type="button" class="pill${f.year===v?" on":""}" data-yr="${v}">${lab} · ${n}</button>`}).join("");
    const rows=base.filter(x=>inYr(x,f.year)).sort((a,b)=>a.r.end-b.r.end||["Confirmed","From term","Estimate"].indexOf(a.r.basis)-["Confirmed","From term","Estimate"].indexOf(b.r.basis)||a.d.deal.localeCompare(b.d.deal));
    state.rRows=rows;
    const firm=rows.filter(x=>x.r.basis!=="Estimate").length;
    $("rcount").textContent=`${rows.length} deal${rows.length===1?"":"s"} · ${firm} confirmed or from term`;
    const shown=rows.slice(0,state.rMore?rows.length:200);
    $("rlist").innerHTML=rows.length?`<div class="tw"><table class="t"><thead><tr><th>Ends</th><th>Basis</th><th>Deal</th><th>Sport</th><th>Category</th><th>Deal type</th><th>Status</th><th>Announced</th></tr></thead><tbody>${shown.map(({d,r})=>`<tr><td><span class="yr">${r.end}</span></td><td>${basisTag(r)}</td><td><span class="dl">${L.pair(d,{px:30})}${S.dealLink(d)}</span></td><td>${esc(d.sport||"")}</td><td>${esc((d._cats||[]).join(", "))}</td><td>${esc(d.tier||"")}</td><td class="d">${esc(d.status||"")}</td><td class="d">${esc(S.fmt(d))}</td></tr>`).join("")}</tbody></table></div>${rows.length>shown.length?`<p><button class="ghost" id="rmore">Show all ${rows.length}</button></p>`:""}`:`<p class="note">Nothing in that window.</p>`;
  };
  let t;$("rq").oninput=e=>{clearTimeout(t);t=setTimeout(()=>{f.q=e.target.value;draw()},150)};
  $("rsport").onchange=e=>{f.sport=e.target.value;draw()};
  $("rcat").onchange=e=>{f.cat=e.target.value;draw()};
  $("rtier").onchange=e=>{f.tier=e.target.value;draw()};
  $("view").onclick=e=>{
    const b=e.target.closest("[data-yr],[data-reg],[data-basis]");
    if(b){if(b.dataset.yr)f.year=b.dataset.yr;if(b.dataset.reg)f.region=b.dataset.reg;if(b.dataset.basis)f.basis=b.dataset.basis;
      b.parentNode.querySelectorAll(".pill").forEach(p=>p.classList.toggle("on",(p.dataset.reg&&p.dataset.reg===f.region)||(p.dataset.basis&&p.dataset.basis===f.basis)||false));draw();return}
    if(e.target.id==="rmore"){state.rMore=true;draw();return}
    if(e.target.id==="rcsv")csv([["Ends","Basis","Deal","Brand","Property","Sport","Category","Deal type","Status","Term (yrs)","Announced","Source"],...state.rRows.map(({d,r})=>[r.end,r.basis,d.deal,nameOf(d),propOf(d),d.sport,(d._cats||[]).join("; "),d.tier,d.status,d.term||"",S.fmt(d),d.url||""])],"sss-pro-renewals.csv");
  };
  draw();
}

/* ---------- Property report ---------- */
function mainSport(p){return [...p.sports.entries()].sort((a,b)=>b[1]-a[1]).map(x=>x[0])[0]||""}
function livePartners(p){
  const m=new Map();
  p.deals.filter(x=>x.side==="p"&&live(x.d)).forEach(x=>(x.other||[]).forEach(b=>{if(b&&!m.has(b.slug))m.set(b.slug,{b,d:x.d,rec:D.orgs.get(b.slug)})}));
  return [...m.values()];
}
function peersOf(p){
  const lg=D.leagues.find(l=>(l.clubs||[]).includes(p.e.slug));
  if(lg)return {label:lg.name,list:lg.clubs.map(s=>D.orgs.get(s)).filter(Boolean)};
  const sp=mainSport(p);
  const list=D.props.filter(x=>x.ptype===p.ptype&&mainSport(x)===sp).sort((a,b)=>b.n-a.n).slice(0,14);
  if(!list.includes(p))list.unshift(p);
  return {label:`${sp} ${p.ptype.toLowerCase()}s`,list};
}
const catOf=b=>(b.rec&&b.rec.cat)||b.b.cat||"Other";
function property(){
  const w=[...watch.get()].map(s=>D.orgs.get(s)).find(r=>r&&r.kind==="property");
  const p=state.p||w||D.orgs.get("collingwood")||D.props[0];state.p=p;
  const sp=mainSport(p);
  const partners=livePartners(p);
  const peers=peersOf(p);
  const have=new Set(partners.map(catOf));
  // Category gaps: categories most peers have a live partner in, that this property doesn't.
  const peerData=peers.list.map(x=>{const lp=livePartners(x);return {x,lp,cats:new Set(lp.map(catOf))}});
  const gapMap=new Map();
  peerData.forEach(pd=>{if(pd.x===p)return;pd.lp.forEach(b=>{const c=catOf(b);if(have.has(c)||c==="Other"||c==="Sport & events")return;const g=gapMap.get(c)||{c,peers:new Set(),brands:new Map()};g.peers.add(pd.x.e.slug);g.brands.set(b.b.slug,b.b);gapMap.set(c,g)})});
  const nPeers=peerData.filter(pd=>pd.x!==p).length||1;
  const gaps=[...gapMap.values()].filter(g=>g.peers.size>=2||nPeers<4).sort((a,b)=>b.peers.size-a.peers.size).slice(0,12);
  // Prospects for a category: brands in it with a live deal in this sport (else ANZ), not already a live partner here.
  const mine=new Set(partners.map(x=>x.b.slug));
  const former=new Set(p.deals.filter(x=>x.side==="p").flatMap(x=>(x.other||[]).filter(Boolean).map(o=>o.slug)));
  const prospects=c=>{
    const score=new Map();
    D.brands.forEach(b=>{if(b.cat!==c||mine.has(b.e.slug))return;
      const ds=b.deals.filter(x=>x.side==="b"&&live(x.d));if(!ds.length)return;
      const inSport=ds.filter(x=>x.d.sport===sp).length, anz=ds.filter(x=>x.d.region==="ANZ").length;
      if(!inSport&&!anz)return;score.set(b.e.slug,{b,s:inSport*10+anz})});
    return [...score.values()].sort((a,b)=>b.s-a.s).slice(0,8);
  };
  const due=p.deals.filter(x=>x.side==="p").map(x=>({d:x.d,r:renewal(x.d)})).filter(x=>x.r&&x.r.end>=yr&&x.r.end<=yr+2).sort((a,b)=>a.r.end-b.r.end);
  const new12=p.deals.filter(x=>monthsAgo(x.d)<=12).length;
  const bench=peerData.map(pd=>{const r=pd.x;const pr=pd.lp;return {r,live:pr.length,new12:r.deals.filter(x=>x.side==="p"&&monthsAgo(x.d)<=12).length,
    major:pr.filter(b=>["Naming rights","Title sponsor","Principal & major"].includes(b.d.tier)).length,cats:pd.cats.size,
    due:r.deals.filter(x=>{const q=renewal(x.d);return x.side==="p"&&q&&q.end>=yr&&q.end<=yr+1}).length}}).sort((a,b)=>b.live-a.live);
  state.pExport={p,partners,gaps,prospects};
  $("view").innerHTML=`<div class="ctl"><input class="srch" id="pq" list="propNames" placeholder="Type a property, e.g. Carlton, Wallabies, NBL" autocomplete="off"><button class="ghost" id="pcsv">Export partner list</button></div>
  <div class="ph">${L.mark(p.e,{px:72})}<div><h2 class="disp">${esc(p.e.name)}</h2><div class="sub">${esc(p.ptype)} · ${esc(sp)} · benchmarked against ${esc(peers.label)} ${star(p.e.slug)}</div></div></div>
  <div class="kpis"><div><b>${partners.length}</b><span>Live partners</span></div><div><b>${new12}</b><span>Deals, last 12 months</span></div><div><b>${have.size}</b><span>Categories covered</span></div><div><b>${due.length}</b><span>Renewals due ${yr}-${yr+2}</span></div></div>
  <p class="note-s">"Live" means the deal's end year hasn't passed, it was announced in the last three years, or the brand is on the club's current partners page.</p>

  <div class="h3">Category gaps and prospects</div>
  <p class="note-s">Categories where at least two ${esc(peers.label)} peers have a live partner and ${esc(p.e.name)} doesn't, with the brands most likely to say yes: live in ${esc(sp)} first, then anywhere in ANZ. A dashed name is a former partner.</p>
  ${gaps.length?`<div class="tw"><table class="t"><thead><tr><th>Category</th><th>Peers with one</th><th>Who they're with</th><th>Prospects</th></tr></thead><tbody>${gaps.map(g=>{const pr=prospects(g.c);return `<tr><td><b>${esc(g.c)}</b></td><td><div class="toolrow"><span class="gapbar"><i style="width:${Math.round(g.peers.size/nPeers*100)}%"></i></span><span class="d">${g.peers.size} of ${nPeers}</span></div></td><td><div class="logos">${[...g.brands.values()].slice(0,6).map(b=>logo(b,28)).join("")}</div></td><td><div class="chips">${pr.map(x=>`<a class="chip${former.has(x.b.e.slug)?" ex":""}" href="${esc(L.page(x.b.e.slug))}">${esc(x.b.e.name)}</a>`).join("")||`<span class="mute-l">None live in the archive yet</span>`}</div></td></tr>`}).join("")}</tbody></table></div>`:`<p class="note">No clear gaps against ${esc(peers.label)}.</p>`}

  <div class="h3">Benchmark: ${esc(peers.label)}</div>
  <div class="tw"><table class="t"><thead><tr><th>Property</th><th>Live partners</th><th>New, last 12 mo</th><th>Naming, title or major</th><th>Categories</th><th>Due ${yr}-${yr+1}</th></tr></thead><tbody>${bench.map(x=>`<tr class="${x.r===p?"me":""}"><td><span class="dl">${logo(x.r.e,30)}<a href="#" data-pick="${esc(x.r.e.slug)}"><b>${esc(x.r.e.name)}</b></a></span></td><td class="d">${x.live}</td><td class="d">${x.new12}</td><td class="d">${x.major}</td><td class="d">${x.cats}</td><td class="d">${x.due}</td></tr>`).join("")}</tbody></table></div>

  <div class="h3">Coming up for renewal</div>
  ${due.length?`<div class="tw"><table class="t"><thead><tr><th>Ends</th><th>Basis</th><th>Deal</th><th>Deal type</th><th>Announced</th></tr></thead><tbody>${due.map(({d,r})=>`<tr><td><span class="yr">${r.end}</span></td><td>${basisTag(r)}</td><td><span class="dl">${L.pair(d,{px:30})}${S.dealLink(d)}</span></td><td>${esc(d.tier||"")}</td><td class="d">${esc(S.fmt(d))}</td></tr>`).join("")}</tbody></table></div>`:`<p class="note-s">Nothing due in the next two years on what's been announced.</p>`}

  <div class="h3">Live partners (${partners.length})</div>
  <div class="tw"><table class="t"><thead><tr><th>Brand</th><th>Category</th><th>Their tier</th><th>Deal type</th><th>Since</th><th>Ends</th></tr></thead><tbody>${partners.sort((a,b)=>S.TIERS.indexOf(a.d.tier)-S.TIERS.indexOf(b.d.tier)||a.b.name.localeCompare(b.b.name)).map(x=>{const r=renewal(x.d);return `<tr><td><span class="dl">${logo(x.b,30)}<a href="${esc(L.page(x.b.slug))}"><b>${esc(x.b.name)}</b></a></span></td><td>${esc(catOf(x))}</td><td>${esc(x.d.ptier||"–")}</td><td>${esc(x.d.tier||"")}</td><td class="d">${esc(S.fmt(x.d))}</td><td class="d">${r?`${r.end} ${basisTag(r)}`:"–"}</td></tr>`}).join("")}</tbody></table></div>`;
  const inp=$("pq");
  inp.onchange=()=>{const v=inp.value.trim().toLowerCase();const r=D.props.find(x=>x.e.name.toLowerCase()===v)||D.props.find(x=>(x.e.aliases||[]).some(a=>a.toLowerCase()===v))||D.props.find(x=>x.e.name.toLowerCase().includes(v));if(r){state.p=r;property();window.scrollTo(0,0)}};
  $("view").onclick=e=>{
    const a=e.target.closest("[data-pick]");if(a){e.preventDefault();state.p=D.orgs.get(a.dataset.pick);property();window.scrollTo(0,0);return}
    if(e.target.id==="pcsv"){const x=state.pExport;csv([["Property","Brand","Category","Their tier","Deal type","Since","Ends","Basis"],...x.partners.map(b=>{const r=renewal(b.d);return [x.p.e.name,b.b.name,catOf(b),b.d.ptier||"",b.d.tier,S.fmt(b.d),r?r.end:"",r?r.basis:""]}),[],["Gap category","Prospects"],...x.gaps.map(g=>[g.c,x.prospects(g.c).map(y=>y.b.e.name).join("; ")])],`sss-pro-${x.p.e.slug}.csv`)}
  };
}

/* ---------- Watchlist ---------- */
function watchlist(){
  const list=[...watch.get()].map(s=>D.orgs.get(s)).filter(Boolean);
  if(!list.length){$("view").innerHTML=`<p class="note">Nothing on your watchlist yet. Tap ☆ next to any brand in the finder, or on a property report, and it'll show up here with its latest deals and upcoming renewals. Your watchlist is saved in this browser.</p>`;return}
  const recentAll=list.flatMap(r=>r.deals.filter(x=>monthsAgo(x.d)<=1).map(x=>x.d));
  const uniq=[...new Map(recentAll.map(d=>[d.deal+(d.date||""),d])).values()];
  $("view").innerHTML=`${uniq.length?`<div class="h3" style="margin-top:0">New in the last month</div><div class="tw"><table class="t"><tbody>${uniq.map(d=>`<tr><td class="d">${esc(S.fmt(d))}</td><td><span class="dl">${L.pair(d,{px:30})}${S.dealLink(d)}</span></td><td>${esc(d.tier||"")}</td><td class="d">${esc(d.status||"")}</td></tr>`).join("")}</tbody></table></div>`:""}
  <div class="h3">Watching ${list.length}</div>
  ${list.map(r=>{const latest=r.deals.slice(0,4);const due=r.deals.map(x=>({d:x.d,q:renewal(x.d)})).filter(x=>x.q&&x.q.end>=yr&&x.q.end<=yr+2).sort((a,b)=>a.q.end-b.q.end).slice(0,4);
    return `<div class="wl"><div><h4>${L.mark(r.e,{px:44})}<a href="${r.kind==="property"?"#":esc(L.page(r.e.slug))}" ${r.kind==="property"?`data-pick="${esc(r.e.slug)}"`:""}>${esc(r.e.name)}</a>${star(r.e.slug)}</h4><div class="sub lbl mute-l" style="margin-top:10px">${r.kind==="property"?esc(r.ptype):esc(r.cat)} · ${r.n} deals</div></div>
    <div><div class="lbl mute-l">Latest</div><ul>${latest.map(x=>`<li>${S.dealLink(x.d)}<span>${esc(S.fmt(x.d))}</span></li>`).join("")}</ul>
    ${due.length?`<div class="lbl mute-l" style="margin-top:16px">Up for renewal</div><ul>${due.map(x=>`<li>${S.dealLink(x.d)}<span>${x.q.end} · ${x.q.basis}</span></li>`).join("")}</ul>`:""}</div></div>`}).join("")}`;
  $("view").onclick=e=>{const a=e.target.closest("[data-pick]");if(a){e.preventDefault();state.p=D.orgs.get(a.dataset.pick);go("property")}};
}

/* ---------- Dashboard (home tab) ---------- */
function dashboard(){
  const inLast=(d,m)=>dated(d)&&monthsAgo(d)<=m&&monthsAgo(d)>=0;
  const ytd=D.deals.filter(d=>dated(d)&&yearOf(d)===yr);
  const anzY=ytd.filter(d=>d.region==="ANZ").length, glY=ytd.length-anzY;
  const share=ytd.length?anzY/ytd.length:0;
  const ry=NOW.getMonth()>=8?yr+1:yr;
  const rAll=D.deals.map(d=>({d,r:renewal(d)})).filter(x=>x.r);
  const due=rAll.filter(x=>x.r.end===ry);
  const dueFirm=due.filter(x=>x.r.basis!=="Estimate");
  const newBrands=D.brands.filter(b=>{const f=b.deals.filter(x=>dated(x.d));return f.length&&f.every(x=>yearOf(x.d)===yr)}).length;
  const anzProps=D.props.filter(p=>p.regions.has("ANZ")).length;

  // Half-circle gauge, same idea as a fund meter: ANZ share of this year's deals.
  const R=88,C=Math.PI*R,arc=`M ${110-R} 104 A ${R} ${R} 0 0 1 ${110+R} 104`;
  const gauge=`<svg viewBox="0 0 220 116" class="gauge" aria-hidden="true"><path d="${arc}" fill="none" stroke="var(--line)" stroke-width="16"/><path d="${arc}" fill="none" stroke="var(--volt)" stroke-width="16" stroke-dasharray="${(C*share).toFixed(1)} ${C.toFixed(1)}"/></svg>`;

  // Last 12 months by announcement month, ANZ and global stacked.
  const months=[];for(let i=11;i>=0;i--){const dt=new Date(yr,NOW.getMonth()-i,1);months.push({k:`${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,"0")}`,lab:dt.toLocaleDateString("en-AU",{month:"short"}),a:0,g:0})}
  const mi=new Map(months.map(m=>[m.k,m]));
  D.deals.forEach(d=>{if(!dated(d))return;const m=mi.get(S.sortKey(d).slice(0,7));if(m)d.region==="ANZ"?m.a++:m.g++});
  const mx=Math.max(1,...months.map(m=>m.a+m.g));
  const W=720,H=220,pb=26,pt=18,bw=W/12;
  const bars=months.map((m,i)=>{const x=i*bw+bw*.18,w=bw*.64,ha=(H-pb-pt)*m.a/mx,hg=(H-pb-pt)*m.g/mx,base=H-pb,cur=i===11;
    return `<g><title>${m.lab}: ${m.a} ANZ, ${m.g} global</title><rect x="${x}" y="${base-ha}" width="${w}" height="${ha}" fill="${cur?"var(--volt)":"var(--ink)"}"${cur?' stroke="var(--ink)" stroke-width="1"':""}/><rect x="${x}" y="${base-ha-hg}" width="${w}" height="${hg}" fill="var(--grey-500)"/>${m.a+m.g?`<text x="${x+w/2}" y="${base-ha-hg-6}" text-anchor="middle" class="bv">${m.a+m.g}</text>`:""}<text x="${x+w/2}" y="${H-6}" text-anchor="middle" class="bl">${m.lab}</text></g>`}).join("");
  const monthChart=`<svg viewBox="0 0 ${W} ${H}" class="mchart" role="img" aria-label="Deals by month, last 12 months"><line x1="0" x2="${W}" y1="${H-pb}" y2="${H-pb}" stroke="var(--ink)" stroke-width="2"/>${bars}</svg>`;

  // Horizontal bar lists for the last 12 months.
  const last12=D.deals.filter(d=>inLast(d,12));
  const tally=f=>{const m=new Map();last12.forEach(d=>[].concat(f(d)).forEach(k=>{if(k&&k!=="Other")m.set(k,(m.get(k)||0)+1)}));return [...m.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8)};
  const hbars=(rows,attr)=>{const top=rows.length?rows[0][1]:1;return `<div class="dhb">${rows.map(([k,n])=>`<button type="button" class="hbr" data-${attr}="${esc(k)}"><span class="hbk">${esc(k)}</span><span class="hbt"><i style="width:${(100*n/top).toFixed(1)}%"></i></span><b>${n}</b></button>`).join("")}</div>`};
  const cats=tally(d=>d._cats), sports=tally(d=>d.sport);

  // Coming up: firm renewal dates first, then estimates, ANZ only.
  const up=rAll.filter(x=>x.d.region==="ANZ"&&x.r.end>=ry&&x.r.end<=ry+1).sort((a,b)=>a.r.end-b.r.end||(a.r.basis==="Estimate")-(b.r.basis==="Estimate")||S.sortKey(b.d).localeCompare(S.sortKey(a.d))).slice(0,7);
  const latest=D.deals.filter(dated).slice(0,7);
  const busy=D.brands.map(b=>({b,n:b.deals.filter(x=>inLast(x.d,12)).length})).filter(x=>x.n>=2).sort((a,b)=>b.n-a.n).slice(0,12);

  $("view").innerHTML=`<div class="dash">
  <div class="dtop">
    <div class="fund">
      <div class="fh"><span>${yr} deals logged</span><span class="vt">${Math.round(share*100)}% ANZ</span></div>
      <div class="gw">${gauge}<div class="gn"><b>${ytd.length.toLocaleString("en-AU")}</b><span>${D.deals.length.toLocaleString("en-AU")} in the archive</span></div></div>
      <div class="ff">${anzY.toLocaleString("en-AU")} ANZ &nbsp;|&nbsp; ${glY.toLocaleString("en-AU")} global</div>
    </div>
    <div class="tiles">
      <a href="#" class="tile" data-go="finder"><span>Brands tracked</span><b>${D.brands.length.toLocaleString("en-AU")}</b><em>${newBrands} new in ${yr}</em></a>
      <a href="#" class="tile" data-go="property"><span>Properties tracked</span><b>${D.props.length.toLocaleString("en-AU")}</b><em>${anzProps.toLocaleString("en-AU")} in ANZ</em></a>
      <a href="#" class="tile" data-go="renewals"><span>Renewals due ${ry}</span><b>${due.length.toLocaleString("en-AU")}</b><em>${dueFirm.length} with a stated end</em></a>
      <a href="#" class="tile" data-go="watch"><span>On your watchlist</span><b>${watch.get().size}</b><em>Brands and properties you follow</em></a>
    </div>
  </div>
  <div class="card">
    <div class="ch"><span class="h3 m0">Deals by month</span><span class="key"><i class="k1"></i>ANZ <i class="k2"></i>Global</span></div>
    ${monthChart}
  </div>
  <div class="two">
    <div class="card"><div class="ch"><span class="h3 m0">Top categories</span><span class="key">Last 12 months</span></div>${hbars(cats,"dcat")}</div>
    <div class="card"><div class="ch"><span class="h3 m0">Busiest sports</span><span class="key">Last 12 months</span></div>${hbars(sports,"dsport")}</div>
  </div>
  <div class="two">
    <div class="card"><div class="ch"><span class="h3 m0">Coming up</span><a href="#" class="more" data-go="renewals">Radar</a></div>
      <ul class="cl">${up.map(({d,r})=>`<li><span class="yr">${r.end}</span><span class="dl">${L.pair(d,{px:28})}${S.dealLink(d)}</span>${basisTag(r)}</li>`).join("")||"<li>None in the archive.</li>"}</ul></div>
    <div class="card"><div class="ch"><span class="h3 m0">Latest deals</span><a href="deals" class="more">Archive</a></div>
      <ul class="cl">${latest.map(d=>`<li><span class="dd">${esc(S.fmt(d).replace(/ \d{4}$/,""))}</span><span class="dl">${L.pair(d,{px:28})}${S.dealLink(d)}</span><span class="chip">${esc(d.sport||"")}</span></li>`).join("")}</ul></div>
  </div>
  <div class="card"><div class="ch"><span class="h3 m0">Most active brands</span><span class="key">Deals, last 12 months</span></div>
    <div class="busy">${busy.map(x=>`<div class="bz">${logo(x.b.e,48)}<a href="${esc(L.page(x.b.e.slug))}">${esc(x.b.e.name)}</a><b>${x.n}</b></div>`).join("")}</div></div>
  </div>`;
  const F=o=>Object.assign({q:"",cat:"",backs:"",notIn:"",region:"All",win:"12",sort:"deals"},o);
  $("view").onclick=e=>{
    const g=e.target.closest("[data-go]");
    if(g){e.preventDefault();go(g.dataset.go);window.scrollTo(0,0);return}
    const c=e.target.closest("[data-dcat]");if(c){state.f=F({cat:c.dataset.dcat});go("finder");window.scrollTo(0,0);return}
    const s=e.target.closest("[data-dsport]");if(s){state.f=F({backs:s.dataset.dsport});go("finder");window.scrollTo(0,0)}
  };
}


/* ---------- Matches: who should partner with whom (pro/matches.json, built by tools/match.py) ---------- */
let MX=null;
/* Feedback on matches: kept in this browser, exported to pro/feedback.json so the engine can learn from it. */
const FKEY="sssPro.feedback";
const fbk={all(){try{return JSON.parse(localStorage.getItem(FKEY)||"{}")}catch(e){return {}}},
  get(p,b){return this.all()[p+"|"+b]||""},
  set(p,b,s){const a=this.all();const k=p+"|"+b;if(a[k]===s)delete a[k];else a[k]=s;try{localStorage.setItem(FKEY,JSON.stringify(a))}catch(e){}return a[k]||""}};
const FB=[["nofit","Not a fit"],["pitched","Pitched"],["won","Won"]];
const fbBtns=(p,b)=>{const cur=fbk.get(p,b);return `<div class="fb" data-fbp="${esc(p)}" data-fbb="${esc(b)}">${FB.map(([k,l])=>`<button type="button" class="fbb${cur===k?" on":""}" data-fb="${k}">${l}</button>`).join("")}</div>`};
const verTag=v=>v?`<span class="basis c" title="Official partners page checked on this date">Verified ${esc(new Date(v+"T00:00:00").toLocaleDateString("en-AU",{day:"numeric",month:"short"}))}</span>`:`<span class="basis" title="This property's official partners page hasn't been checked yet, so its partner list may be incomplete">Not verified yet</span>`;
const mxLoad=()=>MX?Promise.resolve(MX):fetch("pro/matches.json",{cache:"no-store"}).then(r=>r.json()).then(j=>MX=j);
const pct=v=>`${(v*100).toFixed(1).replace(/\.0$/,"")}%`;
const bandCls=k=>k==="Call now"?"c":k==="Strong"?"t":"";
function matches(){
  $("view").innerHTML=`<p class="note">Loading matches…</p>`;
  mxLoad().then(()=>drawMatches()).catch(err=>{console.error(err);$("view").innerHTML=`<p class="note">Couldn't load matches. They're rebuilt each time the archive updates; refresh to try again.</p>`});
}
function slotMap(rec){
  const sl=rec.sl||[];if(!sl.length)return "";
  const lab={open:"Open",ending:"Ending soon",sold:"Sold"};
  const cell=s=>`<div class="sl ${s.st}"><span class="sl-st">${lab[s.st]}${s.e?` · ${s.e}`:""}</span><b>${esc(s.u)}</b><span class="sl-b">${s.b.length?esc(s.b.join(", ")):`${s.a} of ${s.n} peers have one`}</span></div>`;
  const n=k=>sl.filter(s=>s.st===k).length;
  return `<div class="h3">Slot map</div><p class="note-s">Every partner slot this property or its peers have filled. ${n("open")} open, ${n("ending")} ending soon or past their last confirmed date, ${n("sold")} sold. Open slots are sorted by how many peers have filled them.${rec.v?"":" This property isn't verified yet, so some open slots may already be sold."}</p><div class="slmap">${sl.map(cell).join("")}</div>`;
}
function intl(m,rec){
  const list=rec.e||[];
  if(!list.length)return m.side==="p"&&rec.r!=="Local"?`<div class="h3">International brands</div><p class="note-s">No overseas brands stand out for this property yet.</p>`:"";
  const head=m.side==="p"?"International brands that could come in here":"Ways into Australia and New Zealand";
  const lead=m.side==="p"?"Brands that sponsor mostly overseas, with no more than one ANZ deal, active in the last 18 months. They can't show up in the main list (they have no local deals to look alike), so they're scored on the gap here (30), fit with this sport and kind of property overseas (30), how much they sponsor (20), the level they buy at (10) and whether they're entering ANZ now (10). Not backtested yet.":"This brand sponsors mostly overseas. These are the ANZ properties where it fits best as a way in: a gap in its sub-category, plus the sport and kind of property it already backs overseas.";
  return `<div class="h3">${head}</div><p class="note-s">${lead}</p><div class="tw"><table class="t mx"><thead><tr><th>#</th><th>${m.side==="p"?"Brand":"Property"}</th><th>Score</th><th>Why</th></tr></thead><tbody>${list.map((r,i)=>{const slug=m.side==="p"?r.b:r.p,o=D.orgs.get(slug);const sub=m.side==="p"?`${esc(r.c||"")}${r.u?` · ${esc(r.u)}`:""}`:`${esc(r.s)} · ${esc(r.r)}`;
    return `<tr><td class="d">${i+1}</td><td><span class="dl">${o?logo(o.e,34):""}<span><a href="${esc(L.page(slug))}"><b>${esc(r.n)}</b></a><br><span class="mute-l">${sub}</span></span></span></td><td><div class="mx-sc"><b>${r.x}</b></div><span class="gapbar"><i style="width:${r.x}%"></i></span><div class="mute-l mx-f">${esc(r.f)} confidence</div></td><td><ul class="mx-why">${(r.w||[]).map(w=>`<li>${esc(w)}</li>`).join("")}</ul>${(r.g||[]).length?`<div class="chips">${r.g.map(g=>`<span class="chip">${esc(g)}</span>`).join("")}</div>`:""}</td></tr>`}).join("")}</tbody></table></div>`;
}
function drawMatches(){
  const m=state.m||(state.m={side:"p",slug:null});
  const pool=m.side==="p"?MX.props:MX.brands;
  if(!m.slug||!pool[m.slug]){
    const w=[...watch.get()].find(s=>pool[s]);
    m.slug=w||(m.side==="p"?(pool.collingwood?"collingwood":Object.keys(pool)[0]):(pool["coca-cola"]?"coca-cola":Object.keys(pool)[0]));
  }
  const rec=pool[m.slug], bt=MX.backtest, org=D.orgs.get(m.slug);
  const rows=rec.m||[];
  state.mExport={rec,rows,side:m.side};
  $("view").innerHTML=`<p class="pro-intro">${m.side==="p"?"The brands this property should be talking to":"The properties this brand should be talking to"}, ranked by Match Score: how closely the brand's existing deals look like this property (sport, league, region, reach, partners in common), plus whether the property has a gap in that sub-category its peers have filled.</p>
  <p class="note-s">${MX.verified} of ${Object.keys(MX.props).length} properties are verified against their official partners page. Matches for unverified properties may suggest a brand that's already a partner.</p>
  <div class="mx-acc"><b>${pct(bt.top20)}</b><span>of new deals signed ${esc(bt.from)} to ${esc(bt.to)} were in that property's top 20 when we scored the archive as it stood in ${esc(bt.from)}. ${pct(bt.top50)} were in the top 50. The best possible today is ${pct(bt.ceiling)}, because the rest came from brands with no earlier deal in the archive. Treat this as a shortlist with evidence, not a forecast.</span></div>
  <div class="ctl"><div class="pills">${pills("mside",[["p","Property → brands"],["b","Brand → properties"]],m.side)}</div>
  <input class="srch" id="mq" list="mxNames" placeholder="${m.side==="p"?"Type a property, e.g. Carlton, Australian Open":"Type a brand, e.g. Coca-Cola, TikTok"}" autocomplete="off"><datalist id="mxNames">${Object.entries(pool).sort((a,b)=>a[1].n.localeCompare(b[1].n)).map(([,r])=>`<option value="${esc(r.n)}">`).join("")}</datalist>
  <button class="ghost" id="mcsv">Export CSV</button></div>
  <div class="ph">${org?L.mark(org.e,{px:72}):""}<div><h2 class="disp">${esc(rec.n)}</h2><div class="sub">${m.side==="p"?`${verTag(rec.v)} ${esc({club:"Club",body:"League or governing body",event:"Event",national:"National team",athlete:"Athlete",venue:"Venue"}[rec.t]||"Property")} · ${esc(rec.s)} · ${esc(rec.r)} reach`:`${esc(rec.c||"Uncategorised")}${rec.u?` · ${esc(rec.u)}`:""}`} ${star(m.slug)}</div></div></div>
  ${rows.length?`<div class="tw"><table class="t mx"><thead><tr><th>#</th><th>${m.side==="p"?"Brand":"Property"}</th><th>Match</th><th>Why</th><th>Signals</th></tr></thead><tbody>${rows.map((r,i)=>{
    const slug=m.side==="p"?r.b:r.p, o=D.orgs.get(slug), pts=r.p&&m.side==="p"?r.p:r.pt||[];
    const sub=m.side==="p"?`${esc(r.c||"")}${r.u?` · ${esc(r.u)}`:""}`:`${esc(r.s)} · ${esc(r.r)}`;
    return `<tr><td class="d">${i+1}</td>
    <td><span class="dl">${o?logo(o.e,34):""}<span><a href="${esc(L.page(slug))}"><b>${esc(r.n)}</b></a><br><span class="mute-l">${sub}</span></span></span></td>
    <td><div class="mx-sc"><b>${r.x}</b><span class="basis ${bandCls(r.k)}">${esc(r.k)}</span></div><span class="gapbar"><i style="width:${r.x}%"></i></span><div class="mute-l mx-f">${esc(r.f)} confidence</div></td>
    <td><ul class="mx-why">${(r.w||[]).map(w=>`<li>${esc(w)}</li>`).join("")}</ul>${(r.g||[]).length?`<div class="chips">${r.g.map(g=>`<span class="chip${g==="Former partner"?" ex":""}">${esc(g)}</span>`).join("")}</div>`:""}${m.side==="b"?`<div class="mute-l mx-f">${r.v?"Verified":"Not verified yet"}</div>`:""}${fbBtns(m.side==="p"?m.slug:r.p,m.side==="p"?r.b:m.slug)}</td>
    <td class="mx-sig"><span title="Lookalike: out of 85">Fit <b>${pts[1]}</b></span><span title="Sub-category gap: out of 15">Gap <b>${pts[4]}</b></span><span class="mute-l" title="Shown, not scored yet: out of 25">Timing ${pts[0]}</span><span class="mute-l" title="Shown, not scored yet: out of 15">Capacity ${pts[2]}</span><span class="mute-l" title="Shown, not scored yet: out of 15">Appetite ${pts[3]}</span></td></tr>`}).join("")}</tbody></table></div>`:`<p class="note">No matches above 40 yet. ${m.side==="p"?"This property needs more deals in the archive.":"This brand needs more deals in the archive."}</p>`}
  <p class="note-s">Fit (out of 85) and Gap (out of 15) make up the score. Timing, Capacity and Appetite are shown but don't count yet: in testing they made the ranking worse, so they come in once the archive is deep enough to prove them. Hidden: live partners, and brands that clash with a live partner on a firm deal in the same sub-category. ${m.side==="p"?(rec.t==="club"?"Clubs are compared with their league and with clubs in other codes in the same city.":["body","event","national"].includes(rec.t)?"Leagues, governing bodies, events and national teams are compared with the major properties of the same kind across every code.":""):""}</p>
  ${m.side==="p"?slotMap(rec):""}
  ${intl(m,rec)}
  <div class="h3">Your feedback</div><p class="note-s">Mark matches as Not a fit, Pitched or Won. It's saved in this browser. Export it and add it to the repo as pro/feedback.json (or send it to Claude): "Not a fit" pairs are then hidden for good, and Pitched and Won show on the match and count toward the hit rate. ${MX.feedback?`So far: ${MX.feedback.pitched} pitched, ${MX.feedback.won} won, ${MX.feedback.nofit} not a fit.`:""}</p>
  <div class="toolrow"><button class="ghost" id="fbexp">Export feedback (${Object.keys(fbk.all()).length})</button></div>
  <p class="note-s">Rebuilt ${esc(MX.generated)} from the full archive.</p>`;
  const inp=$("mq");
  inp.onchange=()=>{const v=inp.value.trim().toLowerCase();const hit=Object.entries(pool).find(([,r])=>r.n.toLowerCase()===v)||Object.entries(pool).find(([,r])=>r.n.toLowerCase().includes(v));if(hit){m.slug=hit[0];drawMatches();window.scrollTo(0,0)}};
  $("view").onclick=e=>{
    const sd=e.target.closest("[data-mside]");if(sd){m.side=sd.dataset.mside;m.slug=null;drawMatches();return}
    const fb=e.target.closest("[data-fb]");if(fb){const w=fb.closest(".fb");const now=fbk.set(w.dataset.fbp,w.dataset.fbb,fb.dataset.fb);w.querySelectorAll(".fbb").forEach(x=>x.classList.toggle("on",x.dataset.fb===now));const ex=$("fbexp");if(ex)ex.textContent=`Export feedback (${Object.keys(fbk.all()).length})`;return}
    if(e.target.id==="fbexp"){const a=fbk.all();const items=Object.entries(a).map(([k,s])=>{const [p,b]=k.split("|");return {p,b,s,d:new Date().toISOString().slice(0,10)}});const blob=new Blob([JSON.stringify({items},null,1)],{type:"application/json"});const l=document.createElement("a");l.href=URL.createObjectURL(blob);l.download="feedback.json";document.body.appendChild(l);l.click();l.remove();return}
    if(e.target.id==="mcsv"){const x=state.mExport;csv([[x.side==="p"?"Property":"Brand","Rank",x.side==="p"?"Brand":"Property","Match","Band","Confidence","Why","Flags","Fit","Gap","Timing","Capacity","Appetite"],...x.rows.map((r,i)=>{const pts=x.side==="p"?r.p:r.pt;return [x.rec.n,i+1,r.n,r.x,r.k,r.f,(r.w||[]).join("; "),(r.g||[]).join("; "),pts[1],pts[4],pts[0],pts[2],pts[3]]})],`sss-pro-matches-${m.slug}.csv`)}
  };
}

/* ---------- tabs ---------- */
const TABS={dash:dashboard,matches,finder,renewals,property,watch:watchlist};
function go(tab){
  state.tab=TABS[tab]?tab:"dash";
  document.querySelectorAll(".tab").forEach(b=>{b.classList.toggle("on",b.dataset.tab===state.tab);b.setAttribute("aria-selected",b.dataset.tab===state.tab)});
  history.replaceState(null,"","#"+state.tab);
  $("view").onclick=null;
  TABS[state.tab]();
}
$("tabs").onclick=e=>{const b=e.target.closest("[data-tab]");if(!b)return;go(b.dataset.tab)};
// Star buttons work on every tab.
document.addEventListener("click",e=>{const s=e.target.closest("[data-star]");if(!s)return;e.stopPropagation();const on=watch.toggle(s.dataset.star);document.querySelectorAll(`[data-star="${CSS.escape(s.dataset.star)}"]`).forEach(b=>{b.classList.toggle("on",on);b.textContent=on?"★":"☆"})},true);

S.load().then(data=>{
  D=data;
  // Typical term per deal type, from deals that state one (needs 8+ examples, otherwise the overall median).
  const med=a=>{a=[...a].sort((x,y)=>x-y);const m=a.length>>1;return a.length%2?a[m]:Math.round((a[m-1]+a[m])/2)};
  const by=new Map();D.deals.forEach(d=>{if(d.term&&d.tier){if(!by.has(d.tier))by.set(d.tier,[]);by.get(d.tier).push(d.term)}});
  const allT=D.deals.filter(d=>d.term).map(d=>d.term);TYP_ALL=allT.length?med(allT):3;
  by.forEach((v,k)=>{if(v.length>=8)TYP[k]=med(v)});
  $("propNames").innerHTML=D.props.slice().sort((a,b)=>b.n-a.n).slice(0,2000).map(r=>`<option value="${esc(r.e.name)}">`).join("");
  go((location.hash||"#dash").slice(1));
}).catch(err=>{console.error(err);$("view").innerHTML=`<p class="note">Couldn't load the archive. Refresh to try again.</p>`});
})();
