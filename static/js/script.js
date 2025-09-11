(function(){
  function rand(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
  var quotes = ["✨ Believe in yourself — every day is a new chance.","🌱 Small steps every day lead to big results.","🚀 Keep going — progress beats perfection.","🌟 Stay curious, stay creative.","💡 Learn a little every day — it compounds."];
  var emojis = ["🌞","🌸","🚀","🌙","🎉","✨","🔥"];
  function formatTime(d){ return d.toLocaleTimeString([], {hour:'numeric',minute:'2-digit'}); }
  function updateGreeting(){
    var greet = document.getElementById('greet-text');
    var quote = document.getElementById('greet-quote');
    var clock = document.getElementById('tiny-clock');
    var name = 'Guest';
    try{ var display = document.getElementById('display-name'); if(display) name = display.textContent.trim(); }catch(e){}
    var now = new Date(), hr = now.getHours();
    var part = hr<12 ? 'Good morning' : hr<18 ? 'Good afternoon' : 'Good evening';
    if(navigator.language && navigator.language.startsWith('es')){
      part = hr<12 ? 'Buenos días' : hr<18 ? 'Buenas tardes' : 'Buenas noches';
    }
    if(greet) greet.innerHTML = part + ', ' + name + ' <span class="emoji-bounce">'+rand(emojis)+'</span>';
    if(quote) quote.textContent = rand(quotes);
    if(clock) clock.textContent = formatTime(now);
  }
  setInterval(updateGreeting,1000); updateGreeting();
  setInterval(function(){document.querySelectorAll('.emoji-bounce').forEach(el=>{el.classList.add('animated'); setTimeout(()=>el.classList.remove('animated'),900)});},5000);
  setInterval(function(){ var q = document.getElementById('greet-quote'); if(q){ q.style.opacity=0; setTimeout(()=>{ q.textContent = rand(quotes); q.style.opacity=1; },400); } },8000);

  // keepalive ping
  (function keepAlive(){
    var lastActivity = Date.now(); ['mousemove','keydown','touchstart','scroll','click'].forEach(function(ev){ window.addEventListener(ev, function(){ lastActivity = Date.now(); }, {passive:true}); });
    function ping(){ var now = Date.now(); var active = (now-lastActivity) < (1000*60*20); if(document.visibilityState==='visible' && active){ fetch('/_keepalive',{method:'POST', credentials:'same-origin'}).catch(()=>{}); } setTimeout(ping, 30000+Math.random()*60000); }
    setTimeout(ping,2000);
  })();

  // auto-translate: inject Google widget for non-en browsers (best-effort)
  (function autoTranslate(){ var userLang = (navigator.languages && navigator.languages[0])||navigator.language||'en'; var short = userLang.split('-')[0]; if(short && short!=='en'){ window.addEventListener('load', function(){ try{ var s = document.createElement('script'); s.src='https://translate.google.com/translate_a/element.js?cb=__googleTranslateElementInit'; s.async=true; s.defer=true; document.head.appendChild(s); window.__googleTranslateElementInit = function(){ new google.translate.TranslateElement({pageLanguage:'en', autoDisplay:false}, 'google_translate_element'); try{ var sel = document.querySelector('select.goog-te-combo'); if(sel){ sel.value = short; sel.dispatchEvent(new Event('change')); } }catch(e){} }; }catch(e){} }); } })();

})();