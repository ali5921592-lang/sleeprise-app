from pathlib import Path
import json
import re
import shutil

ROOT = Path('/home/ubuntu/sleepify-apk-github')
HTML_PATH = ROOT / 'www/index.html'
html = HTML_PATH.read_text()

# Seed the base language list before the original bootstrap runs. This prevents
# a saved zh/ja/ar/etc. locale from being reset to English on app startup.
LANG_SEED = 'const LANGS=[{c:"tr",f:"🇹🇷",n:"Türkçe",e:"Turkish",loc:"tr-TR",v:"tr-TR"},{c:"en",f:"🇬🇧",n:"English",e:"English",loc:"en-US",v:"en-US"},{c:"es",f:"🇪🇸",n:"Español",e:"Spanish",loc:"es-ES",v:"es-ES"},{c:"de",f:"🇩🇪",n:"Deutsch",e:"German",loc:"de-DE",v:"de-DE"},{c:"fr",f:"🇫🇷",n:"Français",e:"French",loc:"fr-FR",v:"fr-FR"},{c:"pt",f:"🇧🇷",n:"Português",e:"Portuguese",loc:"pt-BR",v:"pt-BR"},{c:"ar",f:"🇸🇦",n:"العربية",e:"Arabic",loc:"ar-SA",v:"ar-SA"},{c:"zh",f:"🇨🇳",n:"简体中文",e:"Chinese",loc:"zh-CN",v:"zh-CN"},{c:"ja",f:"日本語",e:"Japanese",loc:"ja-JP",v:"ja-JP"}]'
html = re.sub(r'const LANGS=\[\{c:"tr".*?\},\{c:"en".*?\}\],I18N=', LANG_SEED + ',I18N=', html, count=1, flags=re.S)

# Keep a reversible source snapshot.
backup = ROOT / 'www/index.v48-backup.html'
if not backup.exists():
    backup.write_text(html)

# Remove the two requested mixer sounds from the source sound list.
html = html.replace('{id:"piano",kind:"piano"},', '')
html = html.replace('{id:"storm",kind:"storm"},', '')

# Make the baby lullaby softer and the hair-dryer ambience less synthetic.
start = html.find('case"lullaby":{')
end = html.find('case"rock":{', start)
if start >= 0 and end > start:
    soft_lullaby = '''case"lullaby":{const e=[261.63,293.66,329.63,392,440,392,329.63,293.66],t=[0,1,2,3,4,3,2,1],a=()=>{const s=t[dummyIndex%t.length];dummyIndex++;const o=n.currentTime,i=n.createOscillator(),r=n.createGain();i.type="sine",i.frequency.value=e[s],r.gain.setValueAtTime(1e-4,o),r.gain.exponentialRampToValueAtTime(.055,o+.08),r.gain.exponentialRampToValueAtTime(1e-4,o+1.45),i.connect(r),r.connect(l),i.start(o),i.stop(o+1.5),c.push(i)};var dummyIndex=0;a(),d=setInterval(a,900);break}'''
    html = html[:start] + soft_lullaby + html[end:]

start = html.find('case"dryer":{')
end = html.find('case"carrain":{', start)
if start >= 0 and end > start:
    realistic_dryer = '''case"dryer":{const e=o("brown"),t=n.createBiquadFilter(),a=n.createBiquadFilter(),s=n.createGain();t.type="lowpass",t.frequency.value=4200,a.type="bandpass",a.frequency.value=1150,a.Q.value=.72,s.gain.value=.42,e.connect(t),t.connect(a),a.connect(s),s.connect(l),e.start(),c.push(e);const r=n.createOscillator(),i=n.createGain(),u=n.createBiquadFilter();r.type="sawtooth",r.frequency.value=92,i.gain.value=.045,u.type="lowpass",u.frequency.value=250,r.connect(u),u.connect(i),i.connect(l),r.start(),c.push(r);const m=n.createOscillator(),h=n.createGain();m.frequency.value=3.8,h.gain.value=.028,m.connect(h),h.connect(s.gain),m.start(),c.push(m);break}'''
    html = html[:start] + realistic_dryer + html[end:]

# Replace phone Web Speech-only breathing helper with a native Android TTS fallback.
old_say_start = html.find('function say(text){')
old_say_end = html.find('function state(){', old_say_start)
if old_say_start >= 0 and old_say_end > old_say_start:
    native_say = '''function say(text){if(!voiceGuide||!text)return;try{if(window.SleepRiseTTS&&window.SleepRiseTTS.speak){window.SleepRiseTTS.speak(String(text),typeof voiceLang==='function'?voiceLang():'tr-TR',1.12);return}if(!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=typeof voiceLang==='function'?voiceLang():'tr-TR',u.rate=1.08,u.pitch=1.02,u.volume=.95,window.speechSynthesis.speak(u)}catch(e){}}'''
    html = html[:old_say_start] + native_say + html[old_say_end:]

# The breathing module in the current HTML calls speak(), not say(). Replace
# both forms so Android native TTS is used on the actual breathing path.
old_speak_start = html.find('function speak(e){')
old_speak_end = html.find('const TASK_IDS', old_speak_start)
if old_speak_start >= 0 and old_speak_end > old_speak_start:
    native_speak = '''function speak(e){try{if(!e)return;if(window.SleepRiseTTS&&window.SleepRiseTTS.speak){window.SleepRiseTTS.speak(String(e),typeof voiceLang==='function'?voiceLang():'tr-TR',1.02);return}if(!('speechSynthesis'in window))return;const t=new SpeechSynthesisUtterance(e);t.lang=typeof voiceLang==='function'?voiceLang():'tr-TR',t.rate=.98,t.pitch=1,speechSynthesis.cancel(),speechSynthesis.speak(t)}catch(e){}}'''
    html = html[:old_speak_start] + native_speak + html[old_speak_end:]

# Expose every bundled alarm MP3 in the alarm picker. The v49 native map
# already uses these IDs, so web preview and native notification stay aligned.
mp3_ids = '["phoneAlarm","electronic1","electronic2","electronic3","piezo1","piezo3","buzzer4","digitalPager","alphaPager","digitalWatch","siren2","siren3","vehicleSiren","evacuation1","evacuation3","mechanicalClock","clockTick5","clockTick3","shortRing","doorbell","industrialBell","rooster","dogs","crow"]'
html = html.replace('TONE_IDS=Object.keys(TONES).concat(WAKE_SYNTH);', 'TONE_IDS=Object.keys(TONES).concat(WAKE_SYNTH,' + mp3_ids + ');')
html = html.replace("function copy(){ return CK[(typeof lang !== 'undefined' && lang === 'en') ? 'en' : 'tr']; }", "function copy(){ return CK[(typeof lang !== 'undefined' && CK[lang]) ? lang : 'tr']; }")
html = html.replace('function toneName(e){if(String(e).startsWith("c:")){const a=cTones.find(t=>"c:"+t.id===e);return a?a.name:t("custom")}return t("tone_"+e)}', 'function toneName(e){if(String(e).startsWith("c:")){const a=cTones.find(t=>"c:"+t.id===e);return a?a.name:t("custom")}return typeof window.SleepRiseV50ToneName==="function"?window.SleepRiseV50ToneName(e):t("tone_"+e)}')
html = html.replace('TONE_IDS.map(e=>`<button data-tn="${e}">${t("tone_"+e)}</button>`', 'TONE_IDS.map(e=>`<button data-tn="${e}">${toneName(e)}</button>`')

# Keep the barcode decoder bundled for Capacitor/offline APK use.
if 'vendor/zxing-browser.min.js' not in html:
    html = html.replace('</head>', '<script src="vendor/zxing-browser.min.js"></script></head>')

# Remove a previously appended v49 layer if this script is rerun.
html = re.sub(r'<script id="sleeprise-v49-layer">.*?</script>\s*', '', html, flags=re.S)

v49 = r'''<script id="sleeprise-v49-layer">
(function(){
  'use strict';
  const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
  const PREF_KEY='sleeprise_v49_preferences';
  let prefs={sleepAmbientEnabled:true,wakeAmbientEnabled:true,voiceGuideEnabled:true};
  try{prefs={...prefs,...JSON.parse(localStorage.getItem(PREF_KEY)||'{}')}}catch(e){}
  const savePrefs=()=>{try{localStorage.setItem(PREF_KEY,JSON.stringify(prefs))}catch(e){}};
  const notifyV49=m=>{try{m=typeof window.SleepRiseV50Text==='function'?window.SleepRiseV50Text(m):m;typeof toast==='function'?toast(m):console.info(m)}catch(e){}};
  const tr={
    es:{name:'Español',sub:'Elige el idioma de SleepRise',sleepAmbient:'Sonido ambiental del sueño',sleepAmbientD:'Permite sonidos y atmósferas durante el modo Sueño.',wakeAmbient:'Sonido ambiental del despertar',wakeAmbientD:'Permite sonidos de fondo durante el modo Despertar.',voiceGuide:'Guía de respiración hablada',voiceGuideD:'Lee las fases de respiración en voz alta.',settings:'Ajustes de sonido',off:'Apagado',on:'Encendido',stop:'Detener',closeAtmosphere:'Cerrar atmósfera',addAlarm:'Añadir alarma',dailyMotivation:'Motivación de hoy',scheduleAlarm:'Programa tu despertar',softLullaby:'Nana suave',mixerOff:'Apagar todos los sonidos',cameraError:'No se pudo abrir la cámara. Comprueba el permiso o introduce el código manualmente.',nativeAlarm:'Alarma guardada en el dispositivo',exactAlarm:'Para una hora exacta, permite Alarmas y recordatorios en Ajustes.'},
    de:{name:'Deutsch',sub:'Wähle die Sprache von SleepRise',sleepAmbient:'Schlaf-Hintergrundton',sleepAmbientD:'Erlaubt Klänge und Atmosphären im Schlafmodus.',wakeAmbient:'Aufwach-Hintergrundton',wakeAmbientD:'Erlaubt Hintergrundklänge im Aufwachmodus.',voiceGuide:'Gesprochene Atemführung',voiceGuideD:'Liest die Atemphasen laut vor.',settings:'Toneinstellungen',off:'Aus',on:'Ein',stop:'Alle Töne stoppen',closeAtmosphere:'Atmosphäre schließen',addAlarm:'Alarm hinzufügen',dailyMotivation:'Motivation des Tages',scheduleAlarm:'Plane dein Aufwachen',softLullaby:'Sanftes Wiegenlied',mixerOff:'Alle Töne ausschalten',cameraError:'Kamera konnte nicht geöffnet werden. Prüfe die Berechtigung oder gib den Code manuell ein.',nativeAlarm:'Alarm auf dem Gerät gespeichert',exactAlarm:'Für genaue Zeiten erlaube Alarme und Erinnerungen in den Einstellungen.'}
  };
  function langText(key, fallback){if(typeof window.SleepRiseV50KeyText==='function'){const x=window.SleepRiseV50KeyText(key);if(x)return x}const l=typeof lang!=='undefined'?lang:'tr';return (tr[l]&&tr[l][key])||fallback||key}
  function addLanguages(){
    try{
      if(typeof LANGS!=='undefined'){
        if(!LANGS.some(x=>x.c==='es'))LANGS.push({c:'es',f:'🇪🇸',n:'Español',e:'Spanish',loc:'es-ES',v:'es-ES'});
        if(!LANGS.some(x=>x.c==='de'))LANGS.push({c:'de',f:'🇩🇪',n:'Deutsch',e:'German',loc:'de-DE',v:'de-DE'});
      }
      if(typeof I18N!=='undefined'){
        I18N.es=I18N.es||{};I18N.de=I18N.de||{};
        Object.assign(I18N.es,{tagline:'Alarma inteligente',tab_alarm:'Alarma',tab_sleep:'Dormir',tab_relax:'Relajarse',tab_day:'Mi día',settings:'Ajustes',add:'Añadir',start:'Iniciar',stopAllS:'Detener todo',sleepTimerT:'Temporizador de sueño',mixerT:'Mezclador de sonidos',listen:'Escuchar',newAlarm:'Nueva alarma',setAlarm:'Configurar alarma',todayT:'Hoy',planT:'Próximos despertares',tipT:'Sugerencia del día',babyT:'Sonidos suaves para bebés',addSoundBtn:'Añadir tu sonido',barcodeReg:'Guardar código de barras'});
        Object.assign(I18N.de,{tagline:'Intelligenter Wecker',tab_alarm:'Alarm',tab_sleep:'Schlaf',tab_relax:'Entspannen',tab_day:'Mein Tag',settings:'Einstellungen',add:'Hinzufügen',start:'Start',stopAllS:'Alle stoppen',sleepTimerT:'Schlaf-Timer',mixerT:'Sound-Mixer',listen:'Anhören',newAlarm:'Neuer Alarm',setAlarm:'Alarm stellen',todayT:'Heute',planT:'Nächste Weckzeiten',tipT:'Tipp des Tages',babyT:'Sanfte Babysounds',addSoundBtn:'Eigenen Sound hinzufügen',barcodeReg:'Barcode speichern'});
      }
      if(typeof renderLangModal==='function')renderLangModal();
      if(typeof renderLangMenu==='function')renderLangMenu();
    }catch(e){console.warn('v49 language',e)}
  }
  function setText(el,txt){if(el)el.textContent=txt}
  function addSettings(){
    const tools=q('#p-tools');if(!tools||q('#v49-settings'))return;
    const card=document.createElement('section');card.id='v49-settings';card.className='v49-settings card';
    card.innerHTML='<div class="v49-settings-head"><div><b>'+langText('settings','Ses ayarları')+'</b><small>Uyku ve uyanış arka plan seslerini istediğin zaman kapat.</small></div><span>⚙</span></div><label class="v49-setting-row"><span><b>Uyku arka planı</b><small>Rahatlama sesleri, atmosfer ve miks</small></span><input type="checkbox" id="v49SleepAmbient" '+(prefs.sleepAmbientEnabled?'checked':'')+'><i></i></label><label class="v49-setting-row"><span><b>Uyanış arka planı</b><small>Uyanış ekranındaki yardımcı sesler</small></span><input type="checkbox" id="v49WakeAmbient" '+(prefs.wakeAmbientEnabled?'checked':'')+'><i></i></label><label class="v49-setting-row"><span><b>Sesli nefes rehberi</b><small>Telefonda da fazları sesli okur</small></span><input type="checkbox" id="v49VoiceGuide" '+(prefs.voiceGuideEnabled?'checked':'')+'><i></i></label><button type="button" class="v49-inline-stop" id="v49ExactAlarm">Android kesin alarm iznini kontrol et</button>';
    tools.insertBefore(card,tools.firstChild);
    const bind=(id,key,after)=>{const el=q('#'+id);if(!el)return;el.addEventListener('change',()=>{prefs[key]=el.checked;savePrefs();after&&after(el.checked);});};
    bind('v49SleepAmbient','sleepAmbientEnabled',onSleepAmbient);
    bind('v49WakeAmbient','wakeAmbientEnabled',v=>{prefs.wakeAmbientEnabled=v;});
    bind('v49VoiceGuide','voiceGuideEnabled',v=>{try{window.SleepifyBreath&&window.SleepifyBreath.setVoice&&window.SleepifyBreath.setVoice(v)}catch(e){}});const exact=q('#v49ExactAlarm');exact&&exact.addEventListener('click',async()=>{const ln=nativePlugin();if(!ln){notifyV49('Bu seçenek yalnızca APK içinde kullanılabilir.');return}try{const s=ln.checkExactNotificationSetting?await ln.checkExactNotificationSetting():null;if(s&&s.status==='granted')notifyV49('Kesin alarm izni açık.');else if(ln.changeExactNotificationSetting)await ln.changeExactNotificationSetting();else notifyV49('Android Ayarlar > Uygulamalar > SleepRise > Alarmlar ve hatırlatıcılar yolunu aç.')}catch(e){notifyV49('Android Ayarlar > Uygulamalar > SleepRise > Alarmlar ve hatırlatıcılar yolunu aç.')}});
  }
  function onSleepAmbient(enabled){
    if(enabled)return;
    try{typeof Mix!=='undefined'&&Mix.stopAll()}catch(e){}
    try{window.SleepRiseAtmosphereV47&&window.SleepRiseAtmosphereV47.stop()}catch(e){}
    qa('[data-v42-stop-relax]').forEach(b=>b.click());
    qa('[data-v42-relax-play]').forEach(b=>b.textContent='BAŞLAT');
    qa('[data-v42-relax-row]').forEach(r=>r.classList.remove('is-playing'));
    notifyV49('Uyku arka plan sesleri kapatıldı');
  }
  function addMixerStop(){
    const grid=q('#mixGrid');if(!grid||q('#v49MixerOff'))return;
    const b=document.createElement('button');b.id='v49MixerOff';b.className='v49-inline-stop';b.textContent=langText('mixerOff','Tüm sesleri kapat');grid.parentElement.insertBefore(b,grid);
    b.addEventListener('click',()=>{try{Mix.stopAll()}catch(e){};qa('[data-v42-stop-relax]').forEach(x=>x.click());qa('[data-v42-relax-play]').forEach(x=>x.textContent='BAŞLAT');qa('[data-v42-relax-row]').forEach(x=>x.classList.remove('is-playing'));notifyV49('Tüm rahatlama sesleri kapatıldı')});
  }
  function addAtmosphereStop(){
    const host=q('#v32Atmospheres')||q('#p-relax');if(!host||q('#v49AtmosphereOff'))return;
    const b=document.createElement('button');b.id='v49AtmosphereOff';b.className='v49-inline-stop';b.textContent=langText('closeAtmosphere','Atmosferi kapat');host.appendChild(b);
    b.addEventListener('click',()=>{try{window.SleepRiseAtmosphereV47&&window.SleepRiseAtmosphereV47.stop()}catch(e){};try{typeof Atm!=='undefined'&&Atm.stop()}catch(e){};q('#cineSw')?.classList.remove('on');q('#cineSw')?.setAttribute('aria-checked','false');notifyV49('Atmosfer kapatıldı')});
  }
  function addWakeCard(){
    const day=q('#p-day');if(!day||q('#v49WakeCard'))return;
    const card=document.createElement('section');card.id='v49WakeCard';card.className='v49-wake-card card';
    card.innerHTML='<div class="v49-wake-kicker">'+langText('dailyMotivation','Günün motivasyonu')+'</div><div class="v49-wake-quote" id="v49WakeQuote"></div><div class="v49-wake-sub">'+langText('scheduleAlarm','Uyanışını bugünden planla.')+'</div><button class="btn primary" id="v49WakeAddAlarm">'+langText('addAlarm','Alarm ekle')+'</button>';
    const first=day.querySelector('.card');first?first.insertAdjacentElement('afterend',card):day.insertBefore(card,day.firstChild);
    const lines={tr:['Bugün kendine iyi davran; küçük bir adım da ilerlemedir.','Uykundan aldığın güç, bugünün en iyi başlangıcı.','Ritmini sen kurarsın; bugün sakin ve kararlı ilerle.','Kendine verdiğin sözleri küçük adımlarla tut.','Bugün yeni bir başlangıç için yeterince iyi bir gün.'],en:['Be kind to yourself today; a small step is still progress.','The energy from your sleep is your best start today.','You set your rhythm; move calmly and steadily.','Keep the promises you make to yourself, one small step at a time.','Today is a good day for a fresh start.'],es:['Sé amable contigo hoy; un pequeño paso también es progreso.','La energía de tu sueño es tu mejor comienzo.','Tú marcas el ritmo; avanza con calma y decisión.','Cumple tus promesas con pequeños pasos.','Hoy es un buen día para empezar de nuevo.'],de:['Sei heute freundlich zu dir; auch ein kleiner Schritt ist Fortschritt.','Die Kraft aus deinem Schlaf ist dein bester Start.','Du bestimmst deinen Rhythmus; geh ruhig und sicher weiter.','Halte deine Versprechen mit kleinen Schritten.','Heute ist ein guter Tag für einen neuen Anfang.']};
    const l=typeof lang!=='undefined'?lang:'tr',arr=lines[l]||lines.tr,now=new Date();setText(q('#v49WakeQuote'),arr[(now.getFullYear()+now.getMonth()+now.getDate())%arr.length]);
    q('#v49WakeAddAlarm').addEventListener('click',()=>{try{q('nav.tabs [data-p="alarm"]')?.click();setTimeout(()=>typeof openSheet==='function'&&openSheet(null),80)}catch(e){}});
  }
  function hideRemovedSounds(){
    qa('[data-snd="piano"],[data-snd="storm"]').forEach(x=>x.remove());
    qa('[data-v42-panel-btn="plans"],[data-v42-panel-btn="profile"],[data-v42-panel="plans"],[data-v42-panel="profile"]').forEach(x=>x.hidden=true);
  }
  function patchRelaxTimer(){
    const el=q('#sleepTimer');if(!el||el.dataset.v49==='1')return;el.dataset.v49='1';
    el.onclick=e=>{const b=e.target.closest('button');if(!b)return;qa('#sleepTimer button').forEach(x=>x.classList.remove('on'));if(el.dataset.active===b.dataset.st){el.dataset.active='';q('#stLeft').textContent='—';return}el.dataset.active=b.dataset.st;b.classList.add('on');let left=Number(b.dataset.st)*60;clearInterval(window.__sr49Timer);const tick=()=>{left--;q('#stLeft').textContent=String(Math.max(0,Math.floor(left/60))).padStart(2,'0')+':'+String(Math.max(0,left%60)).padStart(2,'0');if(left<=0){clearInterval(window.__sr49Timer);el.dataset.active='';qa('#sleepTimer button').forEach(x=>x.classList.remove('on'));stopEveryRelaxSound();q('#stLeft').textContent='—';notifyV49('Tüm rahatlama sesleri kapandı')}};q('#stLeft').textContent=String(Math.floor(left/60)).padStart(2,'0')+':00';window.__sr49Timer=setInterval(tick,1000);notifyV49(b.dataset.st+' dakika sonra tüm rahatlama sesleri kapanacak')};
    q('#mixStop')?.addEventListener('click',()=>{clearInterval(window.__sr49Timer);el.dataset.active='';qa('#sleepTimer button').forEach(x=>x.classList.remove('on'));q('#stLeft').textContent='—'});
  }
  function stopEveryRelaxSound(){try{typeof Mix!=='undefined'&&Mix.stopAll()}catch(e){};try{window.SleepRiseAtmosphereV47&&window.SleepRiseAtmosphereV47.stop()}catch(e){};qa('[data-v42-stop-relax]').forEach(x=>x.click());qa('[data-v42-relax-play]').forEach(x=>x.textContent='BAŞLAT');qa('[data-v42-relax-row]').forEach(x=>x.classList.remove('is-playing'));qa('audio,video').forEach(x=>{try{x.pause();x.currentTime=0}catch(e){}})}
  function patchCamera(){
    if(typeof startScanner!=='function'||window.__sr49ScannerReady)return;
    window.__sr49ScannerReady=true;
    let controls=null,detectorTimer=null,activeVideo=null,activeStream=null,finished=false;
    const stopRobust=()=>{finished=true;clearInterval(detectorTimer);detectorTimer=null;try{controls&&controls.stop&&controls.stop()}catch(e){}controls=null;try{activeStream&&activeStream.getTracks().forEach(t=>t.stop())}catch(e){}activeStream=null;if(activeVideo){try{activeVideo.pause();activeVideo.srcObject=null}catch(e){}activeVideo=null}};
    const patchedStop=()=>{stopRobust();const reg=q('#regScan');if(reg)reg.remove()};
    const patchedStart=async function(video,onCode){stopRobust();finished=false;activeVideo=video;try{if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia)throw new Error('media-not-supported');const constraints={audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}};if(window.ZXingBrowser&&window.ZXingBrowser.BrowserMultiFormatReader){const reader=new window.ZXingBrowser.BrowserMultiFormatReader();controls=await reader.decodeFromConstraints(constraints,video,(result,error)=>{if(result&&!finished){finished=true;const text=String(result.getText?result.getText():result.text||'').trim();if(text)onCode(text);setTimeout(stopRobust,80)}});return controls}activeStream=await navigator.mediaDevices.getUserMedia(constraints);video.srcObject=activeStream;video.setAttribute('playsinline','');video.muted=true;await video.play();if('BarcodeDetector'in window){let detector;try{detector=new window.BarcodeDetector()}catch(e){detector=null}if(detector){detectorTimer=setInterval(async()=>{if(finished||!video.videoWidth)return;try{const hits=await detector.detect(video);if(hits&&hits.length){finished=true;const text=String(hits[0].rawValue||'').trim();if(text)onCode(text);setTimeout(stopRobust,80)}}catch(e){}},300);return true}}throw new Error('barcode-decoder-unavailable')}catch(err){stopRobust();console.warn('SleepRise camera/barcode',err);notifyV49(langText('cameraError','Kamera veya barkod okuyucu açılamadı; kodu elle girebilirsin.'));const hint=q('#bcHint')||q('#barcodeState');if(hint)hint.textContent=langText('cameraError','Kamera veya barkod okuyucu açılamadı; kodu elle girebilirsin.');return null}};
    try{stopScanner=patchedStop}catch(e){}window.stopScanner=patchedStop;
    try{startScanner=patchedStart}catch(e){}window.startScanner=patchedStart;
  }
  function nativePlugin(){return window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.LocalNotifications}
  const toneFiles={phoneAlarm:'phone-alarm.mp3',electronic1:'electronic-buzzer-1.mp3',electronic2:'electronic-buzzer-2.mp3',electronic3:'electronic-buzzer-3.mp3',piezo1:'piezo-alarm-1.mp3',piezo3:'piezo-alarm-3.mp3',buzzer4:'buzzer-4.mp3',digitalPager:'digital-pager.mp3',alphaPager:'alphanumeric-pager.mp3',digitalWatch:'digital-watch-alarm.mp3',siren2:'two-tone-siren.mp3',siren3:'three-tone-siren.mp3',vehicleSiren:'vehicle-siren.mp3',evacuation1:'evacuation-alarm-1.mp3',evacuation3:'evacuation-alarm-3.mp3',mechanicalClock:'mechanical-clock.mp3',clockTick5:'mechanical-clock-tick-5.mp3',clockTick3:'mechanical-clock-tick-3.mp3',shortRing:'mechanical-short-ring.mp3',doorbell:'mechanical-doorbell.mp3',industrialBell:'industrial-doorbell.mp3',rooster:'rooster.mp3',dogs:'barking-dogs.mp3',crow:'crow.mp3'};
  const nativeIds=()=>{try{return JSON.parse(localStorage.getItem('sleeprise_v49_native_ids')||'[]')}catch(e){return[]}};
  const saveNativeIds=x=>{try{localStorage.setItem('sleeprise_v49_native_ids',JSON.stringify(x))}catch(e){}};
  function alarmOccurrences(a,limit=14){const out=[],now=new Date();for(let day=0;day<32&&out.length<limit;day++){const d=new Date(now);d.setDate(now.getDate()+day);d.setHours(a.h,a.m,0,0);if(d<=now)continue;if(!a.days?.length||a.days.includes(d.getDay()))out.push(d)}return out}
  async function syncNativeAlarms(){const ln=nativePlugin();if(!ln||typeof alarms==='undefined')return{ok:false,reason:'not-native'};try{const p=await ln.checkPermissions();if(p.display!=='granted'){const r=await ln.requestPermissions();if(r.display!=='granted'){notifyV49('Bildirim izni verilmedi; alarm uygulama kapalıyken çalışmayabilir.');return{ok:false,reason:'permission'}}}const old=nativeIds();if(old.length)try{await ln.cancel({notifications:old.map(id=>({id}))})}catch(e){}const active=alarms.filter(a=>a.on),notes=[],ids=[];let seq=0;for(const a of active){const base=(toneFiles[a.tone]||toneFiles.phoneAlarm).replace(/\.mp3$/,'').replace(/[^a-z0-9_]/gi,'_').toLowerCase();try{await ln.createChannel({id:'sleeprise_alarm_v53_'+base,name:'SleepRise · '+(a.label||'Alarm'),description:'SleepRise alarm sound',importance:5,sound:base,vibration:true,lights:true})}catch(e){}for(const when of alarmOccurrences(a,a.days?.length?14:1)){const id=300000+(seq++);ids.push(id);notes.push({id,title:'SleepRise · '+String(a.h).padStart(2,'0')+':'+String(a.m).padStart(2,'0'),body:a.label||'Uyanma zamanı geldi.',schedule:{at:when,allowWhileIdle:true},channelId:'sleeprise_alarm_v53_'+base,sound:base,ongoing:true,autoCancel:false,extra:{alarmId:a.id,tone:a.tone,radioUrl:(()=>{try{return JSON.parse(localStorage.getItem('sleeprise_features_v42_radio')||'{}').url||''}catch(e){return ''}})()}})}}if(notes.length)await ln.schedule({notifications:notes});saveNativeIds(ids);try{const ex=ln.checkExactNotificationSetting?await ln.checkExactNotificationSetting():null;if(ex&&ex.status&&ex.status!=='granted')notifyV49(langText('exactAlarm','Android Ayarlar > Uygulamalar > SleepRise > Alarmlar ve hatırlatıcılar iznini aç.'))}catch(e){}if(notes.length)notifyV49(langText('nativeAlarm','Alarm cihazda kaydedildi'));return{ok:true,count:notes.length}}catch(err){console.warn('SleepRise native alarms',err);notifyV49('Cihaz alarmı kaydedilemedi; bildirim izinlerini kontrol et.');return{ok:false,reason:String(err)}}}
  function hookNativeScheduling(){
    const oldRefresh=window.refresh;if(typeof oldRefresh==='function'&&!oldRefresh.__v49){const wrapped=function(){const r=oldRefresh.apply(this,arguments);setTimeout(syncNativeAlarms,120);return r};wrapped.__v49=true;window.refresh=wrapped}
    setTimeout(syncNativeAlarms,1400);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')setTimeout(syncNativeAlarms,300)});
    const ln=nativePlugin();if(ln&&ln.addListener)ln.addListener('localNotificationActionPerformed',ev=>{const x=ev.notification?.extra||{},a=typeof alarms!=='undefined'&&alarms.find(z=>String(z.id)===String(x.alarmId));if(a&&typeof fire==='function')fire(a);if(x.radioUrl){try{const ra=new Audio(x.radioUrl);ra.loop=true;ra.volume=.8;ra.play().catch(()=>notifyV49('Radyo için ekrana dokunarak aç.'))}catch(e){}}});
  }
  function setupRealFire(){
    const grid=q('#mixGrid');if(!grid||grid.dataset.v49fire==='1')return;grid.dataset.v49fire='1';let fireAudio=null;const stop=()=>{if(fireAudio){try{fireAudio.pause();fireAudio.currentTime=0}catch(e){}fireAudio=null}};document.addEventListener('click',e=>{const tap=e.target.closest('[data-tap="fire"]');if(!tap)return;e.preventDefault();e.stopImmediatePropagation();if(fireAudio){stop();return}try{fireAudio=new Audio('audio/fireplace-crackle-cc0.mp3');fireAudio.loop=true;fireAudio.volume=.42;fireAudio.play().catch(()=>notifyV49('Şömine sesini başlatmak için ekrana dokun.'))}catch(err){}},true);document.addEventListener('input',e=>{const v=e.target.closest('[data-vol="fire"]');if(v&&fireAudio)fireAudio.volume=Number(v.value)/100*.65},true);q('#v49MixerOff')?.addEventListener('click',stop);window.addEventListener('pagehide',stop)}
  function addStyles(){if(q('#sleepriseV49Style'))return;const s=document.createElement('style');s.id='sleepriseV49Style';s.textContent=`#v49-settings{margin:0 0 14px;padding:16px;background:linear-gradient(145deg,#172b52,#101b39);border:1px solid rgba(134,230,222,.2);border-radius:20px;color:#fff}.v49-settings-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.v49-settings-head b{display:block;font:800 16px/1.1 Inter,sans-serif}.v49-settings-head small,.v49-setting-row small{display:block;color:#aebbd8;font:500 10px/1.4 Inter,sans-serif;margin-top:4px}.v49-setting-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 0;border-top:1px solid rgba(255,255,255,.08);cursor:pointer}.v49-setting-row b{display:block;color:#fff;font:700 11px/1.1 Inter,sans-serif}.v49-setting-row input{position:absolute;opacity:0}.v49-setting-row i{flex:0 0 42px;height:24px;border-radius:20px;background:#3c4b69;position:relative}.v49-setting-row i:after{content:'';position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.2s}.v49-setting-row input:checked+i{background:#00b899}.v49-setting-row input:checked+i:after{left:21px;background:#102b44}.v49-inline-stop{display:block;width:100%;margin:8px 0;border:1px solid rgba(134,230,222,.3);border-radius:11px;padding:10px;background:rgba(134,230,222,.1);color:#d9fffa;font:800 10px/1 Inter,sans-serif}.v49-wake-card{margin:12px 0;padding:18px!important;background:linear-gradient(145deg,#173e66,#cd704d)!important;color:#fff}.v49-wake-kicker{font:800 10px/1 Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#bff9f0}.v49-wake-quote{margin:10px 0 6px;font:800 19px/1.18 Inter,sans-serif}.v49-wake-sub{color:#e6f4f1;font:500 11px/1.4 Inter,sans-serif;margin-bottom:13px}.v49-wake-card .btn{background:#fff;color:#183b58}.sr47-real-video{object-fit:cover;filter:saturate(1.05) contrast(1.03)}#v32Atmospheres #v49AtmosphereOff{margin-top:12px}.v49-settings input:focus-visible+i,.v49-inline-stop:focus-visible{outline:2px solid #86e6de;outline-offset:2px}`;document.head.appendChild(s)}
  function clearRemovedMixerSounds(){try{if(typeof Mix!=='undefined'){Mix.off&&Mix.off('piano');Mix.off&&Mix.off('storm');}if(typeof mixVols!=='undefined'){delete mixVols.piano;delete mixVols.storm;typeof save==='function'&&save();}}catch(e){}}
  function init(){addLanguages();addSettings();addMixerStop();addAtmosphereStop();addWakeCard();hideRemovedSounds();clearRemovedMixerSounds();patchRelaxTimer();patchCamera();setupRealFire();addStyles();hookNativeScheduling();if(prefs.voiceGuideEnabled===false)try{window.SleepifyBreath&&window.SleepifyBreath.setVoice&&window.SleepifyBreath.setVoice(false)}catch(e){}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,100),{once:true});else setTimeout(init,100);
  window.SleepRiseV49={syncNativeAlarms,stopEveryRelaxSound,prefs};
})();
</script>
'''
html += '\n' + v49

# v50 runtime layer: load the complete local translation bundle, merge every
# existing dictionary, and refresh all visible screens when the user changes
# language. The file is local, so this works offline inside Capacitor.
html = re.sub(r'<script id="sleeprise-v50-layer">.*?</script>\s*', '', html, flags=re.S)
v50 = r'''<script id="sleeprise-v50-layer">
(function(){
  'use strict';
  const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
  const LANG_META={
    es:{f:'🇪🇸',n:'Español',e:'Spanish',loc:'es-ES',v:'es-ES'},
    de:{f:'🇩🇪',n:'Deutsch',e:'German',loc:'de-DE',v:'de-DE'},
    fr:{f:'🇫🇷',n:'Français',e:'French',loc:'fr-FR',v:'fr-FR'},
    pt:{f:'🇧🇷',n:'Português',e:'Portuguese',loc:'pt-BR',v:'pt-BR'},
    ar:{f:'🇸🇦',n:'العربية',e:'Arabic',loc:'ar-SA',v:'ar-SA'},
    zh:{f:'🇨🇳',n:'简体中文',e:'Chinese',loc:'zh-CN',v:'zh-CN'},
    ja:{f:'🇯🇵',n:'日本語',e:'Japanese',loc:'ja-JP',v:'ja-JP'}
  };
  let DATA=__SLEEPRISE_V50_BUNDLE__;
  const current=()=>typeof lang!=='undefined'&&lang?lang:'tr';
  const selected=d=>d&&d[current()];
  const msg=(key,fallback)=>{const d=selected(DATA&&DATA.messages);return d&&d[key]||fallback||key};
  const base=(key)=>{const d=selected(DATA&&DATA.base);return d&&Object.prototype.hasOwnProperty.call(d,key)?d[key]:null};
  const extra=(name,key)=>{const d=DATA&&DATA.extra&&DATA.extra[name]&&DATA.extra[name][current()];return d&&Object.prototype.hasOwnProperty.call(d,key)?d[key]:null};
  window.SleepRiseV50KeyText=key=>msg(key,base(key)||extra('I18N_EXT',key)||null);
  window.SleepRiseV50ToneName=key=>{const d=selected(DATA&&DATA.tones);return d&&d[key]||base('tone_'+key)||key};
  const literal={
    'Uyku arka plan sesleri kapatıldı':'sleepAmbientOff','Tüm rahatlama sesleri kapatıldı':'allRelaxOff','Atmosfer kapatıldı':'atmosphereClosed',
    'Şömine sesini başlatmak için ekrana dokun.':'fireTap','Radyo için ekrana dokun.':'radioTap','Bildirim izni verilmedi; alarm uygulama kapalıyken çalışmayabilir.':'permissionDenied',
    'Alarm cihazda kaydedildi':'nativeAlarm','Kesin alarm izni açık.':'exactAlarmOpen'
  };
  window.SleepRiseV50Text=x=>{const k=literal[x];return k?msg(k,x):x};
  function addLanguages(){
    if(typeof LANGS==='undefined')return;
    Object.entries(LANG_META).forEach(([c,m])=>{if(!LANGS.some(x=>x.c===c))LANGS.push({c,...m})});
  }
  function merge(){
    if(!DATA||typeof I18N==='undefined')return;
    Object.keys(LANG_META).forEach(code=>{
      I18N[code]=I18N[code]||{};
      Object.assign(I18N[code],DATA.base[code]||{},DATA.extra?.I18N_EXT?.[code]||{},DATA.extra?.I18N_OB?.[code]||{},DATA.extra?.I18N_TD?.[code]||{},DATA.extra?.I18N_TOUR?.[code]||{});
    });
    const baseSources={};
    try{if(typeof I18N_EXT!=='undefined')baseSources.I18N_EXT=I18N_EXT;if(typeof I18N_OB!=='undefined')baseSources.I18N_OB=I18N_OB;if(typeof I18N_TD!=='undefined')baseSources.I18N_TD=I18N_TD;if(typeof I18N_TOUR!=='undefined')baseSources.I18N_TOUR=I18N_TOUR}catch(e){}
    Object.keys(baseSources).forEach(name=>{const source=baseSources[name];Object.keys(source).forEach(c=>{if(I18N[c])Object.assign(I18N[c],source[c])})});
    try{if(typeof CK!=='undefined')Object.keys(DATA.extra?.CK||{}).forEach(c=>{CK[c]=DATA.extra.CK[c]})}catch(e){}
    try{
      const legacyTargets={};
      try{if(typeof I18N_MODE!=='undefined')legacyTargets.I18N_MODE=I18N_MODE;if(typeof I18N_V11!=='undefined')legacyTargets.I18N_V11=I18N_V11;if(typeof I18N_A!=='undefined')legacyTargets.I18N_A=I18N_A;if(typeof I18N_ATM!=='undefined')legacyTargets.I18N_ATM=I18N_ATM;if(typeof I18N_ATM2!=='undefined')legacyTargets.I18N_ATM2=I18N_ATM2;if(typeof I18N_BABY!=='undefined')legacyTargets.I18N_BABY=I18N_BABY;if(typeof I18N_V17!=='undefined')legacyTargets.I18N_V17=I18N_V17;if(typeof I18N_VID!=='undefined')legacyTargets.I18N_VID=I18N_VID}catch(e){}
      const full=DATA.legacy?.full||{};Object.keys(full).forEach(name=>{const target=legacyTargets[name];if(!target)return;Object.keys(full[name]).forEach(c=>{target[c]=full[name][c]})});
      const zhOnly=DATA.legacy?.zh_only||{};Object.keys(zhOnly).forEach(name=>{const target=legacyTargets[name];if(target&&zhOnly[name].zh)target.zh=zhOnly[name].zh});
    }catch(e){console.warn('SleepRise v50 legacy locale',e)}
  }
  function updateV49(){
    const m=selected(DATA&&DATA.messages);if(!m)return;
    const head=q('#v49-settings .v49-settings-head b'),desc=q('#v49-settings .v49-settings-head small');if(head)head.textContent=m.settings;if(desc)desc.textContent=m.settingsDesc;
    [['v49SleepAmbient','sleepAmbient','sleepAmbientDesc'],['v49WakeAmbient','wakeAmbient','wakeAmbientDesc'],['v49VoiceGuide','voiceGuide','voiceGuideDesc']].forEach(([id,title,sub])=>{const el=q('#'+id);if(!el)return;const wrap=el.closest('.v49-setting-row');const spans=wrap?wrap.querySelectorAll('span b,span small'):[];if(spans[0])spans[0].textContent=m[title];if(spans[1])spans[1].textContent=m[sub]});
    const set=(sel,key)=>{const el=q(sel);if(el&&m[key])el.textContent=m[key]};
    set('#v49ExactAlarm','exactAlarm');set('#v49MixerOff','mixerOff');set('#v49AtmosphereOff','atmosphereOff');set('#v49WakeCard .v49-wake-kicker','dailyMotivation');set('#v49WakeCard .v49-wake-sub','scheduleAlarm');set('#v49WakeAddAlarm','addAlarm');
    const err=q('#bcHint')||q('#barcodeState');if(err&&/Kamera|barcode|barkod/i.test(err.textContent||''))err.textContent=m.cameraError;
  }
  function refresh(){
    try{addLanguages();merge();if(typeof applyI18n==='function')applyI18n();if(typeof renderLangModal==='function')renderLangModal();if(typeof renderLangMenu==='function')renderLangMenu();if(typeof window.SleepRiseProfessional?.refresh==='function')window.SleepRiseProfessional.refresh();if(typeof renderTones==='function')renderTones();updateV49();document.documentElement.lang=(LANGS.find(x=>x.c===current())||{}).loc||current();document.documentElement.dir=current()==='ar'?'rtl':'ltr'}catch(e){console.warn('SleepRise v50 locale refresh',e)}
  }
  async function boot(){
    try{if(!DATA){const r=await fetch('translations/sleeprise_v50_i18n.json',{cache:'no-store'});if(!r.ok)throw new Error('translation-bundle-'+r.status);DATA=await r.json()}addLanguages();merge();refresh();}catch(e){console.warn('SleepRise v50 translation bundle',e);addLanguages();try{renderLangModal();renderLangMenu()}catch(err){}}
  }
  document.addEventListener('click',e=>{const target=e.target.closest('#langGrid [data-l],#langMenu [data-l]');if(target)setTimeout(refresh,40)},true);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
</script>
'''
translation_bundle = json.loads((ROOT / 'translations/sleeprise_v50_i18n.json').read_text())
v50 = v50.replace('__SLEEPRISE_V50_BUNDLE__', json.dumps(translation_bundle, ensure_ascii=False, separators=(',', ':')))
html += '\n' + v50
HTML_PATH.write_text(html)

# Patch Capacitor config with notification defaults.
config_path = ROOT / 'capacitor.config.json'
config = json.loads(config_path.read_text())
config['plugins'] = {
    **config.get('plugins', {}),
    'LocalNotifications': {
        'iconColor': '#00B899',
        'sound': 'alarm_default.wav',
        'presentationOptions': ['badge', 'sound', 'banner', 'list']
    }
}
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')

# Patch Android manifest permissions required for camera, notifications and exact alarms.
manifest = ROOT / 'android/app/src/main/AndroidManifest.xml'
mt = manifest.read_text()
for perm in [
    'android.permission.POST_NOTIFICATIONS',
    'android.permission.SCHEDULE_EXACT_ALARM',
    'android.permission.WAKE_LOCK',
    'android.permission.RECEIVE_BOOT_COMPLETED'
]:
    line = f'    <uses-permission android:name="{perm}" />\n'
    if perm not in mt:
        mt = mt.replace('    <uses-permission android:name="android.permission.INTERNET" />\n', line + '    <uses-permission android:name="android.permission.INTERNET" />\n')
manifest.write_text(mt)

# Add native Android TTS bridge for WebView breathing guidance.
main_activity = ROOT / 'android/app/src/main/java/com/sleepify/app/MainActivity.java'
java = main_activity.read_text()
if 'import android.webkit.JavascriptInterface;' not in java:
    java = java.replace('import android.webkit.WebView;\n', 'import android.webkit.WebView;\nimport android.webkit.JavascriptInterface;\n')
if 'import android.speech.tts.TextToSpeech;' not in java:
    java = java.replace('import android.webkit.JavascriptInterface;\n', 'import android.webkit.JavascriptInterface;\nimport android.speech.tts.TextToSpeech;\n')
if 'import java.util.Locale;' not in java:
    java = java.replace('import java.util.List;\n', 'import java.util.List;\nimport java.util.Locale;\n')
if 'private TextToSpeech sleepRiseTts;' not in java:
    java = java.replace('    private PermissionRequest pendingMediaRequest;\n', '    private PermissionRequest pendingMediaRequest;\n    private TextToSpeech sleepRiseTts;\n')
needle = '        webView.getSettings().setDomStorageEnabled(true);\n'
insert = '''        webView.getSettings().setDomStorageEnabled(true);\n        sleepRiseTts = new TextToSpeech(this, status -> {\n            if (status == TextToSpeech.SUCCESS) sleepRiseTts.setLanguage(Locale.forLanguageTag("tr-TR"));\n        });\n        webView.addJavascriptInterface(new SleepRiseTtsBridge(), "SleepRiseTTS");\n'''
if needle in java and 'addJavascriptInterface(new SleepRiseTtsBridge()' not in java:
    java = java.replace(needle, insert)
bridge = '''\n    private final class SleepRiseTtsBridge {\n        @JavascriptInterface\n        public void speak(String text, String language, float rate) {\n            runOnUiThread(() -> {\n                if (sleepRiseTts == null || text == null || text.trim().isEmpty()) return;\n                try {\n                    Locale locale = Locale.forLanguageTag(language == null ? "tr-TR" : language.replace('_', '-'));\n                    sleepRiseTts.setLanguage(locale);\n                    sleepRiseTts.setSpeechRate(Math.max(0.65f, Math.min(1.45f, rate)));\n                    sleepRiseTts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "sleeprise-tts");\n                } catch (Exception ignored) { }\n            });\n        }\n\n        @JavascriptInterface\n        public void stop() {\n            runOnUiThread(() -> { if (sleepRiseTts != null) sleepRiseTts.stop(); });\n        }\n    }\n'''
if 'class SleepRiseTtsBridge' not in java:
    java = java.replace('\n    private void handleWebMediaRequest', bridge + '\n    private void handleWebMediaRequest')
if 'public void onDestroy()' not in java:
    java = java.replace('\n    private boolean hasResource', '''\n    @Override\n    public void onDestroy() {\n        if (sleepRiseTts != null) { sleepRiseTts.stop(); sleepRiseTts.shutdown(); }\n        super.onDestroy();\n    }\n\n    private boolean hasResource''')
main_activity.write_text(java)

# iOS local notification foreground behavior and permission delegate.
app_delegate = ROOT / 'ios/App/App/AppDelegate.swift'
swift = app_delegate.read_text()
if 'import UserNotifications' not in swift:
    swift = swift.replace('import Capacitor\n', 'import Capacitor\nimport UserNotifications\n')
swift = swift.replace('        // Override point for customization after application launch.\n        return true', '        UNUserNotificationCenter.current().delegate = self\n        return true')
if 'UNUserNotificationCenterDelegate' not in swift:
    swift += '''\n\nextension AppDelegate: UNUserNotificationCenterDelegate {\n    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {\n        completionHandler([.banner, .sound, .badge])\n    }\n}\n'''
app_delegate.write_text(swift)

# iOS background audio capability for user-started relaxation/radio playback.
plist = ROOT / 'ios/App/App/Info.plist'
pt = plist.read_text()
if '<key>UIBackgroundModes</key>' not in pt:
    pt = pt.replace('</dict>', '  <key>UIBackgroundModes</key>\n  <array>\n    <string>audio</string>\n  </array>\n</dict>')
plist.write_text(pt)

print('v49 web/native patch written')
