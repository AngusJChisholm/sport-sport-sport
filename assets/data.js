/* Shared data for the directory and insight pages.
   Loads deals.json + entities.json once and builds one record per brand or property.
   A name on the left of "Brand × Property" is a brand, on the right a property; anything on both sides
   is filed where it appears most (the same rule profile.html uses). */
window.SSSData=(function(){
  const L=window.SSSLogos;
  const sortKey=d=>d.date||((d.month||"0000-00")+"-00");
  const yearOf=d=>parseInt(sortKey(d).slice(0,4),10)||0;
  const fmt=d=>{if(!d.date&&!d.month)return "Current partner";const o=d.date?new Date(d.date+"T00:00:00"):new Date((d.month||"2026-01")+"-01T00:00:00");
    return d.date?o.toLocaleDateString("en-AU",{day:"2-digit",month:"short",year:"numeric"}):o.toLocaleDateString("en-AU",{month:"short",year:"numeric"})};
  // The order categories and property types are listed in.
  const CATS=["Banking & finance","Insurance","Betting & wagering","Fintech, crypto & trading","Automotive","Telco","Technology","Energy & utilities","Mining & resources","Airlines & travel","Tourism & government","Alcohol","Non-alcoholic drinks","Food & nutrition","Retail","Apparel & footwear","Sporting goods & equipment","Health & beauty","Media & broadcast","Gaming & esports","Construction & property","Home & hardware","Industrial & manufacturing","Logistics & transport","Professional services","Hospitality & entertainment","Education","Watches & luxury","Collectibles & licensing","Agriculture","Not-for-profit","Sport & events","Other"];
  const PTYPES=["Club & team","National team","League & competition","Event","Governing body","Athlete & talent","Venue","Other"];
  const TIERS=["Naming rights","Title sponsor","Principal & major","Kit & apparel","Shirt & kit placement","Official partner","Media & broadcast","Licensing & merchandise","Ambassador & endorsement","Investment & ownership"];
  let P=null;
  function load(){
    if(P)return P;
    P=Promise.all([fetch("deals.json",{cache:"no-store"}).then(r=>r.json()),L.load()]).then(([data])=>{
      const deals=(data.deals||[]).map(d=>L.tag(Object.assign({},d))).sort((a,b)=>sortKey(b).localeCompare(sortKey(a)));
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
      const yr=new Date().getFullYear();
      const all=[...M.values()].map(m=>Object.assign(m,{
        kind:m.nB>=m.nP?"brand":"property",n:m.deals.length,latest:m.deals[0],
        thisYr:m.deals.filter(x=>yearOf(x.d)===yr).length,
        cat:m.e.cat||"Other",ptype:m.e.ptype||"Other",
        hay:[m.e.name,...(m.e.aliases||[]),...[...m.partners.values()].map(p=>p.name)].join(" ").toLowerCase()}));
      // Each deal gets its brands' categories, for category views.
      deals.forEach(d=>{d._cats=[...new Set(d._bs.map(e=>(M.get(e.slug)||{}).cat||e.cat||"Other"))]});
      return {deals,orgs:M,brands:all.filter(m=>m.kind==="brand"),props:all.filter(m=>m.kind==="property"),leagues:L.leagues(),site:data.site||{}};
    });
    return P;
  }
  const esc=L.esc;
  const dealLink=d=>{
    const name=esc(d.deal);
    if(d.slug&&d.article)return `<a href="articles/${encodeURIComponent(d.slug)}.html"><b>${name}</b></a>`;
    if(d.url&&/^https:\/\//.test(d.url))return `<a href="${esc(d.url)}" target="_blank" rel="noopener"><b>${name}</b></a>`;
    return `<b>${name}</b>`;
  };
  const endsTxt=d=>d.ends?`${d.endsEst?"c. ":""}${d.ends}`:"";
  const qs=()=>new URLSearchParams(location.search);
  function setQs(obj){const p=new URLSearchParams();Object.entries(obj).forEach(([k,v])=>{if(v)p.set(k,v)});history.replaceState(null,"",location.pathname+(p.toString()?"?"+p:""))}
  return {load,sortKey,yearOf,fmt,CATS,PTYPES,TIERS,esc,dealLink,endsTxt,qs,setQs};
})();
