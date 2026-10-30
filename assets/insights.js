/* Insights hub (insights.html): headline numbers and simple charts from the deal archive. */
(function(){
const $=id=>document.getElementById(id);
const S=window.SSSData, esc=S.esc;
$("yr").textContent=new Date().getFullYear();
const yr=new Date().getFullYear();
const tip=$("tip");
document.addEventListener("mousemove",e=>{const t=e.target.closest("[data-tip]");if(!t){tip.style.display="none";return}
  tip.innerHTML=t.dataset.tip;tip.style.display="block";const w=tip.offsetWidth;tip.style.left=Math.min(e.clientX+14,innerWidth-w-8)+"px";tip.style.top=(e.clientY+14)+"px"});

// Horizontal bars: rows of [label, value, href]. One series, one colour, so no legend.
function hbars(rows){
  const max=Math.max(1,...rows.map(r=>r[1]));
  return `<div class="hb">${rows.map(([l,v,h])=>`<div class="row" style="display:contents" data-tip="<b>${esc(v)}</b> deals · ${esc(l)}">${h?`<a class="lb" href="${esc(h)}">${esc(l)}</a>`:`<span class="lb">${esc(l)}</span>`}<span class="tr"><span class="br" style="width:${(v/max*100).toFixed(1)}%"></span></span><span class="vl">${v}</span></div>`).join("")}</div>`;
}
const count=(arr,f)=>{const m=new Map();arr.forEach(x=>[].concat(f(x)).forEach(k=>{if(k)m.set(k,(m.get(k)||0)+1)}));return [...m.entries()].sort((a,b)=>b[1]-a[1])};

S.load().then(D=>{
  const deals=D.deals, thisYr=deals.filter(d=>S.yearOf(d)===yr);
  $("heroStats").innerHTML=[[deals.length.toLocaleString("en-AU"),"deals filed"],[thisYr.length.toLocaleString("en-AU"),`deals in ${yr}`],[D.brands.length.toLocaleString("en-AU"),"brands"],[D.props.length.toLocaleString("en-AU"),"properties"]]
    .map(([v,l])=>`<div class="stat"><b>${esc(v)}</b><span>${esc(l)}</span></div>`).join("");

  // Deals per month, last 24 months. Current month highlighted (it's still filling up).
  const now=new Date();const months=[];
  for(let i=23;i>=0;i--){const d=new Date(now.getFullYear(),now.getMonth()-i,1);months.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`)}
  const byM=new Map(months.map(m=>[m,0]));
  deals.forEach(d=>{const k=S.sortKey(d).slice(0,7);if(byM.has(k))byM.set(k,byM.get(k)+1)});
  const mMax=Math.max(1,...byM.values());
  const mlab=m=>new Date(m+"-01T00:00:00").toLocaleDateString("en-AU",{month:"short",year:"numeric"});
  const colsHtml=`<div class="cols">${months.map((m,i)=>`<span class="c${i===months.length-1?" cur":""}" style="height:${(byM.get(m)/mMax*100).toFixed(1)}%" data-tip="<b>${byM.get(m)}</b> deals · ${esc(mlab(m))}${i===months.length-1?" (so far)":""}"></span>`).join("")}</div><div class="cx"><span>${esc(mlab(months[0]))}</span><span>${esc(mlab(months[months.length-1]))}</span></div>`;

  const sp=count(thisYr,d=>d.sport).slice(0,12);
  const cats=count(thisYr,d=>d._cats).filter(([c])=>c!=="Other").slice(0,12).map(([c,v])=>[c,v,`categories.html?c=${encodeURIComponent(c)}`]);
  const tiers=count(thisYr,d=>d.tier).map(([t,v])=>[t,v]);
  const st=count(thisYr,d=>d.status);
  const reg=count(thisYr,d=>d.region);
  const ending=deals.filter(d=>d.ends===yr+1).length;

  $("charts").innerHTML=`
  <div class="chart wide"><span class="lbl mute-l">Deal flow</span><h3>Deals filed per month</h3>${colsHtml}</div>
  <div class="chart"><span class="lbl mute-l">${yr}</span><h3>Top categories</h3>${hbars(cats)}<p style="margin-top:18px"><a class="more" href="categories.html">All categories →</a></p></div>
  <div class="chart"><span class="lbl mute-l">${yr}</span><h3>Top sports</h3>${hbars(sp)}</div>
  <div class="chart"><span class="lbl mute-l">${yr}</span><h3>What brands are buying</h3>${hbars(tiers)}</div>
  <div class="chart"><span class="lbl mute-l">${yr}</span><h3>New money vs renewals</h3>${hbars(st)}
    <h3 style="margin-top:40px">ANZ vs global</h3>${hbars(reg)}
    <p class="note-s" style="margin-top:24px"><b>${ending}</b> deals filed are due to end in ${yr+1}. <a class="more" href="renewals.html?year=${yr+1}">Renewal watch →</a></p></div>`;
}).catch(()=>{$("charts").innerHTML=`<p class="note">Couldn't load the numbers. Refresh to try again.</p>`});
})();
