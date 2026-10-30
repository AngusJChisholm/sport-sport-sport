/* League maps (leagues.html): every club in a league against every sponsor category. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const yr=new Date().getFullYear();
$("yr").textContent=yr;
const q0=S.qs();
const st={league:q0.get("league")||"",span:q0.get("span")||"all"};

S.load().then(D=>{
  const leagues=D.leagues.filter(l=>Array.isArray(l.clubs)&&l.clubs.length);
  if(!leagues.some(l=>l.name===st.league))st.league=leagues[0].name;
  const recentFrom=`${yr-1}-01-01`;
  function draw(){
    const lg=leagues.find(l=>l.name===st.league);
    const clubs=lg.clubs.map(s=>D.orgs.get(s)||{e:L.byId(s)||{slug:s,name:s},deals:[]}).filter(c=>c.e);
    // club slug -> category -> Map(brand slug -> {e, last date})
    const grid=new Map();const catClubs=new Map();
    clubs.forEach(c=>{
      const m=new Map();grid.set(c.e.slug,m);
      (c.deals||[]).filter(x=>x.side==="p"&&(st.span==="all"||S.sortKey(x.d)>=recentFrom||(!x.d.date&&!x.d.month))).forEach(x=>{
        x.d._bs.forEach(b=>{if(!b)return;const rec=D.orgs.get(b.slug);const cat=(rec&&rec.cat)||"Other";
          const cm=m.get(cat)||new Map();if(!cm.has(b.slug))cm.set(b.slug,{e:b,d:x.d});m.set(cat,cm)});
      });
      m.forEach((_,cat)=>catClubs.set(cat,(catClubs.get(cat)||0)+1));
    });
    const cats=[...catClubs.entries()].sort((a,b)=>(a[0]==="Other")-(b[0]==="Other")||b[1]-a[1]).map(x=>x[0]);
    const n=clubs.length;
    $("lgPills").innerHTML=leagues.map(l=>`<button type="button" class="pill${st.league===l.name?" on":""}" data-l="${esc(l.name)}" aria-pressed="${st.league===l.name}">${esc(l.name)}</button>`).join("");
    $("regPills").innerHTML=[["all","All deals filed"],["recent",`Current and since ${yr-1}`]].map(([k,l])=>`<button type="button" class="pill${st.span===k?" on":""}" data-sp="${k}" aria-pressed="${st.span===k}">${l}</button>`).join("");
    $("lgNote").textContent=`${n} ${lg.name} clubs × ${cats.length} categories. A dash means we haven't filed a partner in that category for the club, not that one definitely doesn't exist. Tap a logo for the brand's page.`;
    $("map").innerHTML=cats.length?`<table class="m"><thead><tr><th class="club">${esc(lg.name)}</th>${cats.map(c=>`<th scope="col"><a href="categories.html?c=${encodeURIComponent(c)}">${esc(c)}</a><br><span class="mute-l" style="font-weight:500;letter-spacing:0">${catClubs.get(c)}/${n} clubs</span></th>`).join("")}</tr></thead><tbody>${clubs.map(c=>{const m=grid.get(c.e.slug);return `<tr><th class="club" scope="row"><a href="${esc(L.page(c.e.slug))}">${L.mark(c.e,{px:30})}${esc(c.e.name)}</a></th>${cats.map(cat=>{const cm=m.get(cat);return cm?`<td><span class="cell">${[...cm.values()].slice(0,3).map(x=>`<a class="lga" href="${esc(L.page(x.e.slug))}" title="${esc(x.e.name)} · ${esc(S.fmt(x.d))}" aria-label="${esc(x.e.name)}">${L.mark(x.e,{px:36})}</a>`).join("")}${cm.size>3?`<span class="mute-l" style="font-size:12px">+${cm.size-3}</span>`:""}</span></td>`:`<td class="no"></td>`}).join("")}</tr>`}).join("")}</tbody></table>`:`<p class="note">No deals filed for these clubs yet.</p>`;
    S.setQs({league:st.league,span:st.span!=="all"&&st.span});
  }
  document.querySelector("main").addEventListener("click",e=>{const b=e.target.closest("[data-l],[data-sp]");if(!b)return;if(b.dataset.l)st.league=b.dataset.l;if(b.dataset.sp)st.span=b.dataset.sp;draw()});
  draw();
}).catch(()=>{$("map").innerHTML=`<p class="note">Couldn't load the map. Refresh to try again.</p>`});
})();
