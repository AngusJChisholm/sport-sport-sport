// Partner slots. Fills every [data-partner-slot] on the page from partners.json (site root).
// Slots stay empty (and take no space) if the file is missing, inactive, or a slot isn't set.
(function(){
  var base=new URL("..",document.currentScript.src);
  var esc=function(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})};
  var src=function(p){return new URL(p,base).href};
  var go=function(u){return ' href="'+esc(u)+'" target="_blank" rel="sponsored noopener"'};
  var head=function(n){return '<div class="pt-h"><span class="lbl">Partner</span><span class="pt-n">'+esc(n)+'</span></div>'};
  var R={
    credit:function(p){return '<p class="pt-cr"><span class="lbl">In partnership with</span><a'+go(p.url)+'>'+esc(p.name)+'</a></p>'},
    presented:function(p){return '<p class="pt-pr"><span class="lbl">Presented by</span><a'+go(p.url)+'>'+esc(p.name)+'</a></p>'},
    signoff:function(p){return '<p class="pt-so"><span>This story was brought to you in partnership with <a'+go(p.url)+'><b>'+esc(p.name)+'</b></a></span><a class="pt-c"'+go(p.url)+'>Discover more</a></p>'},
    feature:function(p,s){return '<aside class="pt pt-feat" aria-label="Partner content">'+head(p.name)+'<a class="pt-b"'+go(s.url||p.url)+'><img src="'+esc(src(s.image))+'" alt="'+esc(s.alt)+'" width="1200" height="900" loading="lazy"><span class="pt-t"><span class="pt-hl">'+esc(s.headline)+'</span><span class="pt-l">'+esc(s.line)+'</span><span class="pt-c">'+esc(s.cta||"Discover more")+'</span></span></a></aside>'},
    wide:function(p,s){return '<aside class="pt pt-wide" aria-label="Partner content">'+head(p.name)+'<a class="pt-im"'+go(s.url||p.url)+'><img src="'+esc(src(s.image))+'" alt="'+esc(s.alt)+'" width="1600" height="900" loading="lazy"></a><div class="pt-f"><span class="pt-l">'+esc(s.line)+'</span><a class="pt-c"'+go(s.url||p.url)+'>'+esc(s.cta||"Discover more")+'</a></div></aside>'},
    home:function(p,s){var m=s.imageMobile?'<source media="(max-width:700px)" srcset="'+esc(src(s.imageMobile))+'" width="1600" height="900">':'';
      return '<aside class="pt pt-wide pt-home" aria-label="Partner content">'+head(p.name)+'<a class="pt-im"'+go(s.url||p.url)+'><picture>'+m+'<img src="'+esc(src(s.image))+'" alt="'+esc(s.alt)+'" width="2400" height="800" loading="lazy"></picture></a><div class="pt-f"><span class="pt-l">'+esc(s.line)+'</span><a class="pt-c"'+go(s.url||p.url)+'>'+esc(s.cta||"Discover more")+'</a></div></aside>'}
  };
  fetch(src("partners.json"),{cache:"no-cache"}).then(function(r){return r.ok?r.json():null}).then(function(p){
    if(!p||!p.active||!p.name||!p.url)return;
    document.querySelectorAll("[data-partner-slot]").forEach(function(el){
      var k=el.getAttribute("data-partner-slot"),s=(p.slots||{})[k];
      if(!s||!R[k]||(typeof s==="object"&&!s.image))return;
      el.innerHTML=R[k](p,s);
      el.hidden=false;
      var wrap=el.closest("[data-partner-wrap]");if(wrap)wrap.hidden=false;
    });
  }).catch(function(){});
})();
