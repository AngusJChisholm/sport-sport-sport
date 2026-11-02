/* News page (news.html): every lead deal article and weekend feature, newest first. */
(function(){
const $=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const PAGE=24;
$("yr").textContent=new Date().getFullYear();
const fmt=d=>new Date(d+"T00:00:00").toLocaleDateString("en-AU",{day:"numeric",month:"short",year:"numeric"});
const okImg=s=>/^(https:\/\/|assets\/)/.test(String(s||""));
const imgSrc=s=>/^https:\/\/images\.unsplash\.com\//.test(s)&&!/[?&]w=/.test(s)?s+(s.includes("?")?"&":"?")+"w=1200&q=70&auto=format&fit=crop":s;

let all=[],f="All",shown=PAGE;
const F=[["All","All stories"],["deal","Deal stories"],["feature","Features"],["ANZ","ANZ"],["Global","Global"]];

Promise.all([
  fetch("deals.json",{cache:"no-store"}).then(r=>r.json()),
  fetch("features.json",{cache:"no-store"}).then(r=>r.ok?r.json():{features:[]}).catch(()=>({features:[]}))
]).then(([d,fj])=>{
  const leads=(d.deals||[]).filter(x=>x.slug&&x.article&&x.date).map(x=>({kind:"deal",date:x.date,head:x.headline||x.deal,sub:x.deal,
    stand:(x.article&&x.article.standfirst)||x.summary||"",label:x.sport,region:x.region,image:x.image,slug:x.slug}));
  const feats=(fj.features||[]).filter(x=>x.slug&&x.article&&x.date&&x.headline).map(x=>({kind:"feature",date:x.date,head:x.headline,sub:x.descriptor||"",
    stand:(x.article&&x.article.standfirst)||"",label:x.topic||"Feature",region:x.region,image:x.image,slug:x.slug}));
  all=[...leads,...feats].sort((a,b)=>b.date.localeCompare(a.date)||(a.kind==="feature"?-1:1));
  draw();
}).catch(()=>{$("grid").innerHTML=`<p class="note">Couldn't load the stories. Refresh to try again.</p>`});

const img=(x,big)=>`<div class="im${okImg(x.image)?"":" noimg"}">${okImg(x.image)?`<img src="${esc(imgSrc(x.image))}" alt="" loading="${big?"eager":"lazy"}" decoding="async" onerror="this.parentElement.classList.add('noimg')">`:""}</div>`;
const meta=x=>`<div class="meta"><span class="tag${x.kind==="feature"?" r":""}">${x.kind==="feature"?"Feature":"Deal story"}</span><span>${esc(x.label||"")}</span><span>${esc(fmt(x.date))}</span></div>`;
const href=x=>`articles/${encodeURIComponent(x.slug)}.html`;

function draw(){
  const r=all.filter(x=>f==="All"||x.kind===f||x.region===f);
  const [first,...rest]=r;
  $("lead").innerHTML=first?`<a class="nlead" href="${href(first)}">${img(first,true)}<div>${meta(first)}<h2 class="disp">${esc(first.head)}</h2>${first.stand?`<p>${esc(first.stand)}</p>`:""}<span class="more">Read the story →</span></div></a>`:`<p class="note">No stories here yet.</p>`;
  $("grid").innerHTML=rest.slice(0,shown).map(x=>`<a class="nc" href="${href(x)}">${img(x)}${meta(x)}<h3>${esc(x.head)}</h3>${x.sub&&x.sub!==x.head?`<span class="lbl mute-l" style="font-size:11px">${esc(x.sub)}</span>`:""}${x.stand?`<p>${esc(x.stand)}</p>`:""}</a>`).join("");
  $("moreBtn").hidden=rest.length<=shown;
  $("pills").innerHTML=F.map(([k,l])=>`<button type="button" class="pill${f===k?" on":""}" data-f="${k}" aria-pressed="${f===k}">${l}</button>`).join("");
}
$("pills").onclick=e=>{const b=e.target.closest("[data-f]");if(!b)return;f=b.dataset.f;shown=PAGE;draw()};
$("moreBtn").onclick=()=>{shown+=PAGE;draw()};
})();
