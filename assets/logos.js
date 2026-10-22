/* Brand and club logos for the site.
   entities.json lists every brand and rights holder: name, official domain, optional local logo file.
   Logos come from Brandfetch (hotlinked, as their terms require) once "brandfetch" in entities.json holds a client ID.
   A local file in assets/logos/ always wins. Anything without a logo gets a monogram in its club colours. */
window.SSSLogos=(function(){
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const norm=x=>String(x||"").normalize("NFKD").replace(/[̀-ͯ]/g,"").toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9()]+/g," ").trim();
  const slugify=x=>String(x||"").normalize("NFKD").replace(/[̀-ͯ]/g,"").replace(/\(.*?\)/g," ").toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");
  let ENT={},LOOK={},LEAGUES=[],BF="",CLUBS=[];
  const okId=s=>/^[A-Za-z0-9_-]{4,64}$/.test(s);
  const okDomain=s=>/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(s);
  const okFile=s=>/^assets\/logos\/[\w.-]+\.(png|svg|webp|jpg)$/i.test(s);

  function load(){
    const e=fetch("entities.json",{cache:"no-store"}).then(r=>r.ok?r.json():{}).catch(()=>({}));
    const c=fetch("instagram/colours.json").then(r=>r.ok?r.json():{}).catch(()=>({}));
    return Promise.all([e,c]).then(([ej,cj])=>{
      ENT=ej.entities||{};LEAGUES=ej.leagues||[];BF=okId(String(ej.brandfetch||""))?ej.brandfetch:"";CLUBS=cj.teams||[];
      LOOK={};
      for(const [slug,x] of Object.entries(ENT)){
        LOOK[norm(x.name)]=slug;
        (x.aliases||[]).forEach(a=>{LOOK[norm(a)]=slug});
      }
    });
  }
  // A deal name is "Brand × Property". Returns the two sides.
  const split=deal=>{const p=String(deal||"").split(/\s+[×x]\s+/);return p.length>=2?[p[0].trim(),p.slice(1).join(" × ").trim()]:[String(deal||"").trim(),""]};
  function resolve(name){
    if(!name)return null;
    const slug=LOOK[norm(name)]||slugify(name);
    const x=ENT[slug]||{name};
    return {slug,name:x.name||name,domain:okDomain(String(x.domain||""))?x.domain:"",logo:okFile(String(x.logo||""))?x.logo:"",aliases:x.aliases||[]};
  }
  const byId=slug=>ENT[slug]?resolve(ENT[slug].name):null;
  // Club colours from instagram/colours.json, used for monograms.
  function colours(e){
    const names=[e.name,...(e.aliases||[])].map(n=>norm(n).replace(/\(.*?\)/g," ").replace(/\s+/g," ").trim());
    for(const t of CLUBS)for(const n of t.names||[])if(names.includes(norm(n)))return (t.colours||[]).filter(h=>/^#[0-9a-f]{6}$/i.test(h));
    return [];
  }
  const lum=h=>{const v=h.replace("#","").match(/../g).map(x=>{x=parseInt(x,16)/255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});return .2126*v[0]+.7152*v[1]+.0722*v[2]};
  function initials(name){
    const skip=new Set(["fc","the","of","and","afc","cf","sc","club","f1","team"]);
    const w=String(name).replace(/\(.*?\)/g," ").split(/[\s\-\/·.]+/).filter(x=>x&&!skip.has(x.toLowerCase()));
    const t=(w.length>1?w[0][0]+w[1][0]:(w[0]||"?").slice(0,1));
    return t.toUpperCase();
  }
  function bfUrl(domain,type,px){
    return `https://cdn.brandfetch.io/domain/${encodeURIComponent(domain)}/w/${px}/h/${px}/fallback/404/type/${type}?c=${encodeURIComponent(BF)}`;
  }
  // big=true asks for the wide logo first (profile page header); small marks try the symbol, then the icon.
  function mark(e,opts){
    opts=opts||{};
    if(!e)return "";
    const px=opts.px||96, big=!!opts.big;
    const cols=colours(e);
    let bg="",fg="";
    if(cols.length){const c=cols.find(h=>lum(h)<.9)||cols[0];bg=c;fg=lum(c)>.45?"#000":"#fff"}
    const mono=`<span class="mono"${bg?` style="background:${bg};color:${fg};border-color:${bg}"`:""} aria-hidden="true">${esc(initials(e.name))}</span>`;
    let src="",steps="";
    if(e.logo){src=e.logo}
    else if(BF&&e.domain){
      const order=big?["logo","symbol","icon"]:["symbol","icon"];
      src=bfUrl(e.domain,order[0],px*2);steps=order.slice(1).map(t=>bfUrl(e.domain,t,px*2)).join(" ");
    }
    const img=src?`<img src="${esc(src)}" alt="" loading="lazy" decoding="async" referrerpolicy="strict-origin-when-cross-origin"${steps?` data-next="${esc(steps)}"`:""} onerror="SSSLogos.fail(this)">`:"";
    return `<span class="lg${img?" has-img":""}${big?" lg-big":""}">${mono}${img}</span>`;
  }
  function fail(img){
    const next=(img.dataset.next||"").split(" ").filter(Boolean);
    if(next.length){img.dataset.next=next.slice(1).join(" ");img.src=next[0];return}
    const box=img.parentElement;img.remove();if(box)box.classList.remove("has-img");
  }
  const page=slug=>`profile.html?id=${encodeURIComponent(slug)}`;
  // Linked logo for a deal side.
  function link(e,opts){
    if(!e)return "";
    return `<a class="lga" href="${esc(page(e.slug))}" aria-label="${esc(e.name)}" title="${esc(e.name)}">${mark(e,opts)}</a>`;
  }
  return {load,split,resolve,byId,mark,link,fail,page,esc,leagues:()=>LEAGUES,all:()=>ENT};
})();
