/* Renewal watch (renewals.html): deals by the year their announced term ends. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const yr=new Date().getFullYear();
$("yr").textContent=yr;
const q0=S.qs();
const st={q:q0.get("q")||"",sport:q0.get("sport")||"",tier:q0.get("tier")||"",region:q0.get("region")||"All",year:q0.get("year")||String(yr)};

S.load().then(D=>{
  // Only deals still running (or ending this year) and announced at least a year ago or with a stated end.
  const all=D.deals.filter(d=>d.ends&&d.ends>=yr);
  const later=yr+3;
  const yrs=[String(yr),String(yr+1),String(yr+2),"later"];
  const inYr=(d,y)=>y==="later"?d.ends>=later:d.ends===+y;
  const sports=[...new Set(all.map(d=>d.sport))].sort();
  const tiers=S.TIERS.filter(t=>all.some(d=>d.tier===t));
  $("sport").innerHTML=`<option value="">All sports</option>`+sports.map(s=>`<option${s===st.sport?" selected":""}>${esc(s)}</option>`).join("");
  $("tier").innerHTML=`<option value="">All deal types</option>`+tiers.map(s=>`<option${s===st.tier?" selected":""}>${esc(s)}</option>`).join("");
  $("q").value=st.q;
  function draw(){
    const q=st.q.trim().toLowerCase();
    const base=all.filter(d=>(!q||d.deal.toLowerCase().includes(q))&&(!st.sport||d.sport===st.sport)&&(!st.tier||d.tier===st.tier)&&(st.region==="All"||d.region===st.region));
    const r=base.filter(d=>inYr(d,st.year)).sort((a,b)=>a.ends-b.ends||(a.endsEst?1:0)-(b.endsEst?1:0)||a.deal.localeCompare(b.deal));
    $("yrPills").innerHTML=yrs.map(y=>{const n=base.filter(d=>inYr(d,y)).length;const lab=y==="later"?`${later}+`:y===String(yr)?`Ending ${y}`:y;return `<button type="button" class="pill${st.year===y?" on":""}" data-y="${y}" aria-pressed="${st.year===y}">${lab} · ${n}</button>`}).join("");
    $("regPills").innerHTML=["All","ANZ","Global"].map(x=>`<button type="button" class="pill${st.region===x?" on":""}" data-r="${x}" aria-pressed="${st.region===x}">${x==="All"?"Everywhere":x}</button>`).join("");
    const stated=r.filter(d=>!d.endsEst).length;
    $("count").textContent=`${r.length} deal${r.length===1?"":"s"} · ${stated} with a stated end date`;
    $("list").innerHTML=r.length?`<div class="tw"><table class="t"><thead><tr><th>Ends</th><th>Deal</th><th>Sport</th><th>Deal type</th><th>Term</th><th>Announced</th><th>Region</th></tr></thead><tbody>${r.map(d=>`<tr><td><span class="yr">${d.ends}</span>${d.endsEst?` <span class="est" title="Worked out from the term and announcement date">c.</span>`:""}</td><td><span class="dl">${L.pair(d,{px:34})}${S.dealLink(d)}</span></td><td>${esc(d.sport)}</td><td>${esc(d.tier||"")}</td><td class="d">${d.term?d.term+(d.term===1?" yr":" yrs"):"–"}</td><td class="d">${esc(S.fmt(d))}</td><td><span class="tag r">${esc(d.region)}</span></td></tr>`).join("")}</tbody></table></div>`:`<p class="note">No deals match that filter.</p>`;
    S.setQs({year:st.year!==String(yr)&&st.year,q:st.q,sport:st.sport,tier:st.tier,region:st.region!=="All"&&st.region});
  }
  let t;$("q").oninput=e=>{clearTimeout(t);t=setTimeout(()=>{st.q=e.target.value;draw()},120)};
  $("sport").onchange=e=>{st.sport=e.target.value;draw()};
  $("tier").onchange=e=>{st.tier=e.target.value;draw()};
  document.querySelector("main").addEventListener("click",e=>{const b=e.target.closest("[data-y],[data-r]");if(!b)return;if(b.dataset.y)st.year=b.dataset.y;if(b.dataset.r)st.region=b.dataset.r;draw()});
  draw();
}).catch(()=>{$("list").innerHTML=`<p class="note">Couldn't load the deals. Refresh to try again.</p>`});
})();
