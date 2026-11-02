/* Shareable league map poster (map.html?league=AFL): a few headline categories for every club, with live logos.
   Built from deals.json and entities.json, so it updates whenever the data does. Current partners and deals
   from last year on only. Fast food is picked by brand name; the other columns use the entities.json category. */
(function(){
const $=id=>document.getElementById(id);
const L=window.SSSLogos, S=window.SSSData, esc=S.esc;
const yr=new Date().getFullYear();
$("yr").textContent=yr;
const FAST=new Set(["mcdonald-s","kfc","hungry-jack-s","domino-s","subway","guzman-y-gomez","red-rooster","nando-s","grill-d","zambrero","oporto","chicken-treat","pizza-hut","burger-king","taco-bell","carl-s-jr","el-jannah","schnitz","muzz-buzz"]);
const COLS=[
  {k:"fast",t:"Fast food",f:(s,cat)=>FAST.has(s)},
  {k:"car",t:"Automotive",f:(s,cat)=>cat==="Automotive"},
  {k:"app",t:"Apparel",f:(s,cat)=>cat==="Apparel & footwear"},
  {k:"alc",t:"Alcohol",f:(s,cat)=>cat==="Alcohol"}];
const MAX=2;
// Brands roll up to their owner (entities.json "parent") when counting clubs.
const grp=e=>(e&&e.parent)||e.slug;
const owner=e=>{if(!e||!e.parent)return "";const p=L.byId(e.parent);return p?(p.short||p.name):""};
const st={league:S.qs().get("league")||"AFL"};
const from=`${yr-1}-01-01`;

S.load().then(D=>{
  const leagues=D.leagues.filter(l=>Array.isArray(l.clubs)&&l.clubs.length);
  if(!leagues.some(l=>l.name===st.league))st.league=leagues[0].name;
  function draw(){
    const lg=leagues.find(l=>l.name===st.league);
    const clubs=lg.clubs.map(s=>D.orgs.get(s)||{e:L.byId(s)||{slug:s,name:s},deals:[]}).filter(c=>c.e);
    // club -> column -> Map(brand slug -> {e, current})
    const grid=new Map(); const count=new Map();
    clubs.forEach(c=>{
      const row={}; COLS.forEach(col=>row[col.k]=new Map());
      (c.deals||[]).filter(x=>x.side==="p"&&(x.d.listed&&!x.d.date&&!x.d.month||S.sortKey(x.d)>=from||(x.d.ends||0)>=yr)).forEach(x=>{
        x.d._bs.forEach(b=>{if(!b)return;const rec=D.orgs.get(b.slug);const cat=(rec&&rec.cat)||b.cat||"Other";
          COLS.forEach(col=>{if(col.f(b.slug,cat)&&!row[col.k].has(b.slug))row[col.k].set(b.slug,{e:b,cur:!!x.d.listed})});
        });
      });
      // Count each company once per club: Carlton Draught and CUB at the same club are one CUB deal.
      const seen=new Set();COLS.forEach(col=>row[col.k].forEach(x=>{const g=grp(x.e);if(!seen.has(g)){seen.add(g);count.set(g,(count.get(g)||0)+1)}}));
      grid.set(c.e.slug,row);
    });
    // Brands at 3+ clubs get the volt marker.
    const hot=e=>(count.get(grp(e))||0)>=3;
    const n=clubs.length;
    document.title=`Who backs who in the ${lg.name} | Sport Sport Sport`;
    $("ph").innerHTML=`Who backs who<br>in the <span class="v">${esc(lg.name)}.</span>`;
    $("lgPills").innerHTML=leagues.map(l=>`<button type="button" class="pill${st.league===l.name?" on":""}" data-l="${esc(l.name)}" aria-pressed="${st.league===l.name}">${esc(l.name)}</button>`).join("");
    const filled=k=>clubs.filter(c=>grid.get(c.e.slug)[k].size).length;
    const cell=m=>{
      if(!m.size)return `<td class="e">-</td>`;
      const list=[...m.values()].sort((a,b)=>hot(b.e)-hot(a.e)||b.cur-a.cur).slice(0,MAX);
      return `<td>${list.map(x=>`<a class="br${hot(x.e)?" hot":""}" href="${esc(L.page(x.e.slug))}">${L.mark(x.e,{px:32})}<span><b>${esc(x.e.name)}</b>${owner(x.e)&&owner(x.e)!==x.e.name?`<small class="own">${esc(owner(x.e))}</small>`:""}</span></a>`).join("")}</td>`;
    };
    $("pt").innerHTML=`<thead><tr><th>Club</th>${COLS.map(c=>`<th scope="col">${c.t}<small>${filled(c.k)}/${n} clubs</small></th>`).join("")}</tr></thead><tbody>${
      clubs.map(c=>{const r=grid.get(c.e.slug);return `<tr><td class="c"><a href="${esc(L.page(c.e.slug))}">${L.mark(c.e,{px:30})}${esc(c.e.name)}</a></td>${COLS.map(col=>cell(r[col.k])).join("")}</tr>`}).join("")}</tbody>`;
    const top=[...count.entries()].filter(([s])=>(count.get(s)||0)>=3).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([s,k])=>`${esc((L.byId(s)||{name:s}).name)}: ${k} clubs`);
    $("pkey").innerHTML=`<i></i>Backs 3 or more clubs${top.length?` (${top.join(", ")})`:""}. Beer brands are counted under the brewer that owns them (e.g. Carlton Draught under CUB), but shown as each club names them. Current partners from each club's official partners page, plus deals announced since ${yr-1} or still running. A dash means nothing filed yet. Updated ${new Date().toLocaleDateString("en-AU",{month:"short",year:"numeric"})}.`;
    S.setQs({league:st.league});
  }
  $("lgPills").addEventListener("click",e=>{const b=e.target.closest("[data-l]");if(!b)return;st.league=b.dataset.l;draw()});
  draw();
}).catch(()=>{$("pt").innerHTML=`<tr><td class="e">Couldn't load the map. Refresh to try again.</td></tr>`});
})();
