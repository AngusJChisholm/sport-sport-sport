/* Brands and Properties directories (brands.html, properties.html).
   Built live from deals.json: every name on the left of "Brand × Property" is a brand, every name on the right a property.
   Anything that shows up on both sides is filed wherever it appears most, the same rule profile.html uses. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, esc=L.esc;
const KIND=document.body.dataset.kind==="properties"?"properties":"brands";
const IS_B=KIND==="brands";
const PAGE=100;
const sortKey=d=>d.date||((d.month||"0000-00")+"-00");
const yr=new Date().getFullYear();
$("yr").textContent=yr;

const qs=new URLSearchParams(location.search);
const st={q:qs.get("q")||"",sport:qs.get("sport")||"All",region:qs.get("region")||"All",league:qs.get("league")||"",sort:qs.get("sort")||"deals",shown:PAGE};

function save(){
  const p=new URLSearchParams();
  if(st.q)p.set("q",st.q);if(st.sport!=="All")p.set("sport",st.sport);if(st.region!=="All")p.set("region",st.region);
  if(st.league)p.set("league",st.league);if(st.sort!=="deals")p.set("sort",st.sort);
  history.replaceState(null,"",location.pathname+(p.toString()?"?"+p:""));
}

Promise.all([fetch("deals.json",{cache:"no-store"}).then(r=>r.json()),L.load()]).then(([data])=>{
  const deals=(data.deals||[]).map(d=>L.tag(Object.assign({},d))).sort((a,b)=>sortKey(b).localeCompare(sortKey(a)));
  // One record per organisation, with how often it sits on each side.
  const M=new Map();
  deals.forEach(d=>{
    const add=(e,side,other)=>{if(!e||!e.slug)return;
      let m=M.get(e.slug);
      if(!m){m={e,nB:0,nP:0,sports:new Map(),regions:new Set(),deals:[],partners:new Map()};M.set(e.slug,m)}
      side==="b"?m.nB++:m.nP++;
      if(d.sport)m.sports.set(d.sport,(m.sports.get(d.sport)||0)+1);
      if(d.region)m.regions.add(d.region);
      m.deals.push({d,side,other});
      (other||[]).forEach(o=>{if(o)m.partners.set(o.slug,o)});
    };
    d._bs.forEach(e=>add(e,"b",d._ps));
    d._ps.forEach(e=>add(e,"p",d._bs));
  });
  const rows=[...M.values()].filter(m=>IS_B?m.nB>=m.nP:m.nP>m.nB).map(m=>{
    const n=m.deals.length, latest=m.deals[0];
    const topSport=[...m.sports.entries()].sort((a,b)=>b[1]-a[1])[0];
    const thisYr=m.deals.filter(x=>sortKey(x.d).startsWith(String(yr))).length;
    return {...m,n,latest,thisYr,topSport:topSport?topSport[0]:"",key:L.esc(m.e.name).toLowerCase(),
      hay:[m.e.name,...(m.e.aliases||[]),...[...m.partners.values()].map(p=>p.name)].join(" ").toLowerCase()};
  });

  // League chips (properties only): AFL, NRL, A-Leagues... from entities.json.
  const leagues=IS_B?[]:L.leagues().filter(l=>Array.isArray(l.clubs)&&l.clubs.length);
  const sports=[...rows.reduce((c,r)=>{r.sports.forEach((v,k)=>c.set(k,(c.get(k)||0)+v));return c},new Map()).entries()].sort((a,b)=>b[1]-a[1]).map(x=>x[0]);

  // Hero numbers.
  const totalDeals=new Set(rows.flatMap(r=>r.deals.map(x=>x.d))).size;
  $("heroStats").innerHTML=[[rows.length.toLocaleString("en-AU"),IS_B?"brands":"properties"],[totalDeals.toLocaleString("en-AU"),"deals filed"],[sports.length,"sports"]]
    .map(([v,l])=>`<div class="stat"><b>${esc(v)}</b><span>${esc(l)}</span></div>`).join("");

  // Most active this year: the top ten by deals filed in the current year.
  const hot=[...rows].filter(r=>r.thisYr).sort((a,b)=>b.thisYr-a.thisYr||a.e.name.localeCompare(b.e.name)).slice(0,10);
  $("hotYr").textContent=yr;
  $("hot").innerHTML=hot.map((r,i)=>`<a href="${esc(L.page(r.e.slug))}"><span class="r">${String(i+1).padStart(2,"0")}</span>${L.mark(r.e,{px:48})}<b>${esc(r.e.name)}</b><span class="c">${r.thisYr} deal${r.thisYr===1?"":"s"} in ${yr}</span></a>`).join("");
  $("band").hidden=!hot.length;

  // Controls.
  $("sport").innerHTML=["All",...sports].map(s=>`<option value="${esc(s)}"${s===st.sport?" selected":""}>${s==="All"?"All sports":esc(s)}</option>`).join("");
  $("sort").value=st.sort;$("q").value=st.q;
  const pills=()=>{
    const reg=["All","ANZ","Global"].map(r=>`<button type="button" class="pill${st.region===r?" on":""}" data-r="${r}" aria-pressed="${st.region===r}">${r==="All"?"Everywhere":r}</button>`).join("");
    $("regPills").innerHTML=reg;
    if(leagues.length)$("lgPills").innerHTML=[`<button type="button" class="pill${!st.league?" on":""}" data-l="" aria-pressed="${!st.league}">All properties</button>`,...leagues.map(l=>`<button type="button" class="pill${st.league===l.name?" on":""}" data-l="${esc(l.name)}" aria-pressed="${st.league===l.name}">${esc(l.name)} clubs</button>`)].join("");
  };

  function draw(){
    const q=st.q.trim().toLowerCase();
    const lg=leagues.find(l=>l.name===st.league);
    const inLg=lg?new Set(lg.clubs):null;
    let r=rows.filter(x=>(!q||x.hay.includes(q))&&(st.sport==="All"||x.sports.has(st.sport))&&(st.region==="All"||x.regions.has(st.region))&&(!inLg||inLg.has(x.e.slug)));
    const by={deals:(a,b)=>b.n-a.n||a.e.name.localeCompare(b.e.name),
      latest:(a,b)=>sortKey(b.latest.d).localeCompare(sortKey(a.latest.d))||b.n-a.n,
      az:(a,b)=>a.e.name.localeCompare(b.e.name,"en",{sensitivity:"base"})};
    r.sort(by[st.sort]||by.deals);
    $("count").textContent=`${r.length.toLocaleString("en-AU")} ${IS_B?(r.length===1?"brand":"brands"):(r.length===1?"property":"properties")}`;
    $("grid").innerHTML=r.slice(0,st.shown).map(x=>{
      const o=(x.latest.other||[]).filter(Boolean).map(e=>e.name).join(" / ");
      const lt=o?`Latest: with ${o}`:"";
      return `<a class="dt" href="${esc(L.page(x.e.slug))}">${L.mark(x.e,{px:72})}<b>${esc(x.e.name)}</b><span class="n">${x.n} deal${x.n===1?"":"s"}</span><span class="k">${esc([...x.sports.keys()].slice(0,2).join(" · "))}</span>${lt?`<span class="lt">${esc(lt)}</span>`:""}</a>`;
    }).join("")||`<p class="note">Nothing matches that. Try a different name or clear the filters.</p>`;
    $("moreBtn").hidden=r.length<=st.shown;
    $("moreBtn").textContent=`Show more (${(r.length-st.shown).toLocaleString("en-AU")} left)`;
    pills();save();
  }
  let t;
  $("q").oninput=e=>{clearTimeout(t);t=setTimeout(()=>{st.q=e.target.value;st.shown=PAGE;draw()},120)};
  $("sport").onchange=e=>{st.sport=e.target.value;st.shown=PAGE;draw()};
  $("sort").onchange=e=>{st.sort=e.target.value;draw()};
  $("regPills").onclick=e=>{const b=e.target.closest("[data-r]");if(!b)return;st.region=b.dataset.r;st.shown=PAGE;draw()};
  $("lgPills").onclick=e=>{const b=e.target.closest("[data-l]");if(!b)return;st.league=b.dataset.l;st.shown=PAGE;draw()};
  $("moreBtn").onclick=()=>{st.shown+=PAGE;draw()};
  draw();
}).catch(()=>{$("grid").innerHTML=`<p class="note">Couldn't load the directory. Refresh to try again.</p>`});
})();
