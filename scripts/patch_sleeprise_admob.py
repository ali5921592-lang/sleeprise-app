from pathlib import Path
import re

ROOT = Path('/home/ubuntu/sleepify-apk-github')
HTML_PATH = ROOT / 'www/index.html'
MANIFEST_PATH = ROOT / 'android/app/src/main/AndroidManifest.xml'
STRINGS_PATH = ROOT / 'android/app/src/main/res/values/strings.xml'
MAIN_ACTIVITY_PATH = ROOT / 'android/app/src/main/java/com/sleepify/app/MainActivity.java'
INFO_PLIST_PATH = ROOT / 'ios/App/App/Info.plist'

ANDROID_APP_ID = 'ca-app-pub-7996356702191225~8756079069'
ANDROID_BANNER_ID = 'ca-app-pub-7996356702191225/8863890276'
ANDROID_REWARDED_ID = 'ca-app-pub-7996356702191225/2298481923'
IOS_APP_ID = 'ca-app-pub-7996356702191225~9135353011'
IOS_BANNER_ID = 'ca-app-pub-7996356702191225/3360282152'
IOS_REWARDED_ID = 'ca-app-pub-7996356702191225/9302873978'

STYLE_MARKER = '<style id="sleeprise-admob-v51-style">'
SCRIPT_MARKER = '<script id="sleeprise-admob-v51">'

STYLE = r'''<style id="sleeprise-admob-v51-style">
:root{--sr-ad-safe-space:0px}
.pages.sr-ad-safe{padding-bottom:calc(var(--sr-ad-safe-space) + 18px)!important}
.v32-atm-card{position:relative}
.sr-ad-atm-gate{position:absolute;left:9px;right:9px;bottom:9px;z-index:6;display:flex;align-items:center;justify-content:center;min-height:30px;padding:7px 10px;border:1px solid rgba(255,255,255,.34);border-radius:11px;background:rgba(6,20,43,.82);backdrop-filter:blur(8px);color:#fff;font:800 10px/1.2 Inter,system-ui,sans-serif;letter-spacing:.01em;box-shadow:0 8px 22px rgba(0,0,0,.24);cursor:pointer}
.sr-ad-atm-gate:focus-visible{outline:2px solid #8af2df;outline-offset:2px}
.sr-ad-pro-card{margin:12px 0;padding:16px;border-radius:20px;background:linear-gradient(135deg,#0d3150,#146b72 60%,#00b899);color:#fff;box-shadow:0 14px 30px rgba(0,91,103,.18)}
.sr-ad-pro-card b{display:block;font-size:16px;letter-spacing:-.02em}.sr-ad-pro-card p{margin:7px 0 12px;color:rgba(255,255,255,.82);font-size:11px;line-height:1.45}.sr-ad-pro-card button{border:0;border-radius:12px;padding:10px 13px;background:#fff;color:#0b4f5c;font:800 12px/1 Inter,system-ui,sans-serif;cursor:pointer}.sr-ad-pro-card button:focus-visible{outline:2px solid #fff;outline-offset:2px}.sr44-cinema-overlay .sr44-cinema-bottom{bottom:calc(12px + var(--sr-ad-safe-space))!important}
@media(prefers-reduced-motion:reduce){.sr-ad-atm-gate,.sr-ad-pro-card{animation:none!important;transition:none!important}}
</style>'''

SCRIPT = r'''<script id="sleeprise-admob-v51">
(function(){
  'use strict';
  const CONFIG=Object.freeze({
    android:{appId:'ca-app-pub-7996356702191225~8756079069',banner:'ca-app-pub-7996356702191225/8863890276',rewarded:'ca-app-pub-7996356702191225/2298481923'},
    ios:{appId:'ca-app-pub-7996356702191225~9135353011',banner:'ca-app-pub-7996356702191225/3360282152',rewarded:'ca-app-pub-7996356702191225/9302873978'},
    rewardHours:24
  });
  const TEXT={
    tr:{watch:'Özelliği açmak için bu reklamı izlemek ister misin?',watchThree:'Uyku analizini açmak için 3 kısa reklam izlenecek. Her reklamdan sonra devam edip etmemeyi seçebilirsin.',watchShort:'Reklamı izle · Aç',adUnavailable:'Reklam şu anda hazır değil. Lütfen biraz sonra tekrar dene.',adCancelled:'Reklam izlenmedi; özellik açılmadı.',bannerNote:'SleepRise’i destekleyen küçük bir reklam',proTitle:'SleepRise Pro',proBody:'Tüm reklamları kaldır, ödüllü beklemeleri atla ve sakin deneyimini koru.',proCta:'Pro’yu keşfet',proPending:'Pro aboneliği mağaza ürünleri tanımlandıktan sonra burada açılacak.',privacy:'Gizlilik tercihleri'},
    en:{watch:'Watch this ad to unlock the feature?',watchThree:'Three short ads are required to unlock sleep analysis. You can stop after each ad.',watchShort:'Watch ad · Unlock',adUnavailable:'The ad is not ready yet. Please try again shortly.',adCancelled:'The ad was not watched; the feature stayed locked.',bannerNote:'A small ad supporting SleepRise',proTitle:'SleepRise Pro',proBody:'Remove every ad, skip rewarded waits, and keep your calm experience.',proCta:'Explore Pro',proPending:'Pro becomes available here after store products are configured.',privacy:'Privacy choices'},
    es:{watch:'¿Ver este anuncio para desbloquear la función?',watchThree:'Se necesitan tres anuncios cortos para desbloquear el análisis del sueño. Puedes detenerte después de cada anuncio.',watchShort:'Ver anuncio · Abrir',adUnavailable:'El anuncio aún no está disponible. Inténtalo de nuevo pronto.',adCancelled:'No se vio el anuncio; la función permanece bloqueada.',bannerNote:'Un pequeño anuncio que apoya SleepRise',proTitle:'SleepRise Pro',proBody:'Elimina todos los anuncios y conserva una experiencia tranquila.',proCta:'Descubrir Pro',proPending:'Pro estará disponible aquí cuando se configuren los productos de la tienda.',privacy:'Preferencias de privacidad'},
    de:{watch:'Werbung ansehen, um die Funktion freizuschalten?',watchThree:'Zum Freischalten der Schlafanalyse werden drei kurze Anzeigen benötigt. Nach jeder Anzeige kannst du aufhören.',watchShort:'Werbung ansehen · Öffnen',adUnavailable:'Die Anzeige ist noch nicht bereit. Bitte versuche es gleich noch einmal.',adCancelled:'Die Anzeige wurde nicht angesehen; die Funktion bleibt gesperrt.',bannerNote:'Eine kleine Anzeige zur Unterstützung von SleepRise',proTitle:'SleepRise Pro',proBody:'Alle Anzeigen entfernen und eine ruhige Nutzung behalten.',proCta:'Pro entdecken',proPending:'Pro wird hier verfügbar, sobald die Store-Produkte eingerichtet sind.',privacy:'Datenschutzeinstellungen'},
    fr:{watch:'Regarder cette annonce pour débloquer la fonction ?',watchThree:'Trois courtes annonces sont nécessaires pour débloquer l’analyse du sommeil. Vous pouvez arrêter après chaque annonce.',watchShort:'Voir l’annonce · Ouvrir',adUnavailable:'L’annonce n’est pas encore prête. Réessayez dans un instant.',adCancelled:'L’annonce n’a pas été regardée ; la fonction reste verrouillée.',bannerNote:'Une petite annonce qui soutient SleepRise',proTitle:'SleepRise Pro',proBody:'Supprimez toutes les annonces et gardez une expérience apaisante.',proCta:'Découvrir Pro',proPending:'Pro sera disponible ici lorsque les produits de la boutique seront configurés.',privacy:'Préférences de confidentialité'},
    pt:{watch:'Assistir a este anúncio para desbloquear o recurso?',watchThree:'Três anúncios curtos são necessários para desbloquear a análise do sono. Você pode parar após cada anúncio.',watchShort:'Assistir anúncio · Abrir',adUnavailable:'O anúncio ainda não está pronto. Tente novamente em instantes.',adCancelled:'O anúncio não foi assistido; o recurso continua bloqueado.',bannerNote:'Um pequeno anúncio que apoia o SleepRise',proTitle:'SleepRise Pro',proBody:'Remova todos os anúncios e mantenha uma experiência tranquila.',proCta:'Conhecer o Pro',proPending:'O Pro ficará disponível aqui após a configuração dos produtos da loja.',privacy:'Preferências de privacidade'},
    ar:{watch:'هل تريد مشاهدة هذا الإعلان لفتح الميزة؟',watchThree:'يلزم مشاهدة ثلاثة إعلانات قصيرة لفتح تحليل النوم. يمكنك التوقف بعد كل إعلان.',watchShort:'شاهد الإعلان · فتح',adUnavailable:'الإعلان غير جاهز الآن. حاول مرة أخرى بعد قليل.',adCancelled:'لم تتم مشاهدة الإعلان؛ بقيت الميزة مقفلة.',bannerNote:'إعلان صغير لدعم SleepRise',proTitle:'SleepRise Pro',proBody:'أزل جميع الإعلانات وحافظ على تجربة هادئة.',proCta:'اكتشف Pro',proPending:'سيصبح Pro متاحاً هنا بعد إعداد منتجات المتجر.',privacy:'خيارات الخصوصية'},
    zh:{watch:'观看此广告以解锁功能吗？',watchThree:'观看三个短广告即可解锁睡眠分析。每个广告结束后都可以停止。',watchShort:'观看广告 · 解锁',adUnavailable:'广告暂时未准备好，请稍后再试。',adCancelled:'未观看广告，功能仍保持锁定。',bannerNote:'支持 SleepRise 的小广告',proTitle:'SleepRise Pro',proBody:'移除所有广告，跳过奖励等待，保持安静的体验。',proCta:'了解 Pro',proPending:'商店商品配置完成后，Pro 将在此处开放。',privacy:'隐私选项'},
    ja:{watch:'広告を見て機能を解放しますか？',watchThree:'睡眠分析を解放するには短い広告を3本見る必要があります。各広告の後に停止できます。',watchShort:'広告を見る · 解放',adUnavailable:'広告を準備できませんでした。少し待ってから再試行してください。',adCancelled:'広告を見なかったため、機能はロックされたままです。',bannerNote:'SleepRiseを支える小さな広告',proTitle:'SleepRise Pro',proBody:'すべての広告を削除し、報酬広告の待ち時間をなくします。',proCta:'Proを見る',proPending:'ストアの商品設定が完了すると、ここでProを利用できます。',privacy:'プライバシー設定'}
  };
  const q=s=>document.querySelector(s), qa=s=>Array.from(document.querySelectorAll(s));
  const langCode=()=>{const raw=(document.documentElement.lang||'').slice(0,2).toLowerCase();return TEXT[raw]?raw:(typeof lang!=='undefined'&&TEXT[lang]?lang:'en')};
  const tx=(key)=>((TEXT[langCode()]||TEXT.en)[key]||TEXT.en[key]||key);
  const native=()=>!!(window.Capacitor&&typeof window.Capacitor.isNativePlatform==='function'&&window.Capacitor.isNativePlatform());
  const admob=()=>window.Capacitor?.Plugins?.AdMob||null;
  const platform=()=>window.Capacitor?.getPlatform?.()||(/iPad|iPhone|iPod/.test(navigator.userAgent)?'ios':'android');
  const isDebug=()=>{try{return !!window.SleepRiseBuild?.isDebug?.()}catch(e){return false}};
  const isPro=()=>{try{return localStorage.getItem('sleeprise_pro_active')==='1'||localStorage.getItem('sleeprise_pro')==='1'||window.SleepRiseSubscription?.isPro?.()===true}catch(e){return false}};
  const trialKey='sleeprise_trial_started_at_v63',trialDays=7;
  const trialStarted=()=>{try{let v=Number(localStorage.getItem(trialKey)||0);if(!v){v=Date.now();localStorage.setItem(trialKey,String(v))}return v}catch(e){return Date.now()}};
  const trialActive=()=>Date.now()<trialStarted()+trialDays*24*60*60*1000;
  const unit=()=>{const p=platform()==='ios'?'ios':'android';return CONFIG[p]};
  const note=msg=>{try{if(typeof notice==='function')return notice(msg);if(typeof toast==='function')return toast(msg);window.alert(msg)}catch(e){}};
  const safeSpace=on=>{document.documentElement.style.setProperty('--sr-ad-safe-space',on?'72px':'0px');q('.pages')?.classList.toggle('sr-ad-safe',!!on)};
  let initialized=false, bannerOn=false, consentInfo=null, busy=false;
  async function init(){
    const api=admob();
    if(!native())return true;
    if(!api){note(tx('adUnavailable'));return false}
    if(initialized)return true;
    try{
      consentInfo=await api.requestConsentInfo?.({})||{canRequestAds:true};
      if(consentInfo.status==='REQUIRED'&&consentInfo.isConsentFormAvailable)consentInfo=await api.showConsentForm?.()||consentInfo;
      if(api.trackingAuthorizationStatus){try{const ti=await api.trackingAuthorizationStatus();if(ti?.status==='notDetermined')await api.requestTrackingAuthorization?.()}catch(e){}}
      if(consentInfo.canRequestAds===false)return false;
      await api.initialize?.({maxAdContentRating:'General'});
      initialized=true;
      return true;
    }catch(e){console.warn('SleepRise AdMob init',e);return false}
  }
  async function showBanner(){
    if(isPro()||trialActive())return removeBanner();
    const api=admob();
    if(!native()||!api)return false;
    if(!(await init()))return false;
    try{await api.showBanner({adId:unit().banner,adSize:'ADAPTIVE_BANNER',position:'BOTTOM_CENTER',margin:0,isTesting:isDebug()});bannerOn=true;safeSpace(true);return true}catch(e){console.warn('SleepRise banner',e);return false}
  }
  async function removeBanner(){
    const api=admob();
    if(api&&native()){try{await api.removeBanner?.()}catch(e){}}
    bannerOn=false;safeSpace(false);
  }
  async function showRewarded(){
    if(!native()||trialActive())return true;
    const api=admob();
    if(!api||!(await init()))return false;
    try{
      await api.prepareRewardVideoAd({adId:unit().rewarded,isTesting:isDebug(),immersiveMode:true});
      const reward=await api.showRewardVideoAd();
      return !!reward&&(Number(reward.amount||0)>0||typeof reward.amount==='undefined');
    }catch(e){console.warn('SleepRise rewarded',e);note(tx('adUnavailable'));return false}
  }
  async function rewardAccess(purpose,count){
    if(isPro()||trialActive())return true;
    const key='sleeprise_reward_until_'+purpose;
    if(purpose==='sleep-analysis'&&Number(localStorage.getItem(key)||0)>Date.now())return true;
    if(!native())return true;
    if(busy)return false;
    busy=true;
    try{
      for(let i=0;i<count;i++){
        const prompt=count>1?tx('watchThree'):tx('watch');
        if(!window.confirm(prompt)){note(tx('adCancelled'));return false}
        if(!(await showRewarded()))return false;
      }
      if(purpose==='sleep-analysis')localStorage.setItem(key,String(Date.now()+CONFIG.rewardHours*60*60*1000));
      return true;
    }finally{busy=false}
  }
  async function guard(purpose,count,action){const ok=await rewardAccess(purpose,count);if(!ok)return false;try{await action();return true}catch(e){console.warn('SleepRise gated action',e);return false}}
  function currentPage(){return q('.pages .page.on')?.id||''}
  async function syncBanner(){
    const should=currentPage()==='p-relax'&&!isPro()&&!trialActive();
    if(should&&!bannerOn)await showBanner();
    if(!should&&bannerOn)await removeBanner();
    decorateAtmosphereGates();bindRelaxTimers();injectProCard();
  }
  function decorateAtmosphereGates(){
    const cards=qa('#v32Atmospheres [data-v32-atm]');
    cards.forEach(card=>{
      const old=card.querySelector('.sr-ad-atm-gate');
      if(isPro()||trialActive()){old?.remove();return;}
      if(old)return;
      const gate=document.createElement('span');gate.className='sr-ad-atm-gate';gate.setAttribute('role','button');gate.setAttribute('tabindex','0');gate.textContent=tx('watchShort');
      const unlock=ev=>{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation?.();guard('atmosphere',1,async()=>{gate.remove();card.click()})};
      gate.addEventListener('click',unlock);gate.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){unlock(ev)}});card.appendChild(gate);
    });
  }
  const relaxTimers=new WeakMap();
  function bindRelaxTimers(){
    qa('[data-v42-relax-play],[data-sr44-relax-play]').forEach(btn=>{
      if(btn.__srAdBound)return;btn.__srAdBound=true;
      btn.addEventListener('click',()=>{
        clearTimeout(relaxTimers.get(btn));
        if(isPro()||trialActive())return;
        const timer=setTimeout(async()=>{
          const row=btn.closest('[data-v42-relax-row],[data-sr44-relax-card]');
          if(!row||!row.classList.contains('is-playing'))return;
          try{btn.click()}catch(e){}
          const ok=await rewardAccess('relax-continued',1);
          if(ok&&!isPro())try{btn.click()}catch(e){}
        },300000);
        relaxTimers.set(btn,timer);
      });
    });
  }
  function injectProCard(){
    const tools=q('#p-tools');if(!tools||q('#srAdProCard'))return;
    const card=document.createElement('section');card.id='srAdProCard';card.className='sr-ad-pro-card';
    card.innerHTML='<b>'+tx('proTitle')+'</b><p>'+tx('proBody')+'</p><button type="button" id="srAdProCta">'+tx('proCta')+'</button>';
    tools.insertBefore(card,tools.firstChild);
    card.querySelector('button').addEventListener('click',()=>{if(window.SleepRiseSubscription?.open)window.SleepRiseSubscription.open();else note(tx('proPending'))});
  }
  function gateClick(e){
    const target=e.target?.closest?.('#btnSession,#btnOwnVid,#btnAddMixSound,#btnAddTone');
    if(!target||target.dataset.srAdBypass==='1')return;
    if(target.id==='btnSession'){
      let open=false;try{open=!!Sleep.open}catch(err){}
      if(!open)return;
      e.preventDefault();e.stopImmediatePropagation();
      guard('sleep-analysis',3,async()=>{target.dataset.srAdBypass='1';target.click();delete target.dataset.srAdBypass});
      return;
    }
    const inputMap={btnOwnVid:'#atmVidFile',btnAddMixSound:'#mixFile',btnAddTone:'#toneFile'};
    const input=q(inputMap[target.id]);if(!input)return;
    e.preventDefault();e.stopImmediatePropagation();
    guard('file-upload',3,async()=>input.click());
  }
  document.addEventListener('click',gateClick,true);
  document.addEventListener('click',e=>{if(e.target?.closest?.('nav.tabs [data-p]'))setTimeout(syncBanner,220)},false);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(syncBanner,180)});
  const observer=new MutationObserver(()=>{decorateAtmosphereGates();bindRelaxTimers();injectProCard()});
  function start(){
    try{observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']})}catch(e){}
    setTimeout(()=>{init().catch(()=>{});syncBanner().catch(()=>{})},700);
    setInterval(()=>{const active=currentPage()==='p-relax'&&!isPro()&&!trialActive();if(active&&!bannerOn)showBanner();if(!active&&bannerOn)removeBanner();decorateAtmosphereGates();bindRelaxTimers();injectProCard()},2500);
  }
  window.SleepRiseAds={config:CONFIG,isPro,trialActive,init,showBanner,removeBanner,showRewarded,rewardAccess,guard,privacy:async()=>{const api=admob();if(api?.showPrivacyOptionsForm)try{return api.showPrivacyOptionsForm()}catch(e){}}};
  window.SleepRiseSubscription=window.SleepRiseSubscription||{isPro,open:()=>note(tx('proPending'))};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
</script>'''


def upsert_html(html: str) -> str:
    html = re.sub(r'<style id="sleeprise-admob-v51-style">.*?</style>', '', html, flags=re.S)
    html = re.sub(r'<script id="sleeprise-admob-v51">.*?</script>', '', html, flags=re.S)
    if '</body>' not in html:
        raise RuntimeError('index.html body kapanış etiketi bulunamadı')
    return html.replace('</body>', STYLE + '\n' + SCRIPT + '\n</body>', 1)


def upsert_android():
    text = MANIFEST_PATH.read_text()
    if 'com.android.vending.BILLING' not in text:
        text = text.replace('    <uses-permission android:name="android.permission.INTERNET" />', '    <uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="com.android.vending.BILLING" />')
    if 'com.google.android.gms.ads.APPLICATION_ID' not in text:
        text = re.sub(r'(<application\b[^>]*>)', r'\1\n        <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="@string/admob_app_id" />', text, count=1)
    MANIFEST_PATH.write_text(text)
    strings = STRINGS_PATH.read_text()
    line = f'    <string name="admob_app_id">{ANDROID_APP_ID}</string>'
    strings = re.sub(r'\s*<string name="admob_app_id">.*?</string>', '', strings)
    strings = strings.replace('</resources>', line + '\n</resources>')
    STRINGS_PATH.write_text(strings)


def upsert_main_activity():
    java = MAIN_ACTIVITY_PATH.read_text()
    bridge = '''\n    private final class SleepRiseBuildBridge {\n        @JavascriptInterface\n        public boolean isDebug() { return (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0; }\n    }\n'''
    if 'class SleepRiseBuildBridge' not in java:
        java = java.replace('\n    private void handleWebMediaRequest', bridge + '\n    private void handleWebMediaRequest')
    if 'addJavascriptInterface(new SleepRiseBuildBridge()' not in java:
        java = java.replace('webView.addJavascriptInterface(new SleepRiseTtsBridge(), "SleepRiseTTS");', 'webView.addJavascriptInterface(new SleepRiseTtsBridge(), "SleepRiseTTS");\n        webView.addJavascriptInterface(new SleepRiseBuildBridge(), "SleepRiseBuild");')
    MAIN_ACTIVITY_PATH.write_text(java)


def upsert_ios():
    text = INFO_PLIST_PATH.read_text()
    pbx = ROOT / 'ios/App/App.xcodeproj/project.pbxproj'
    project = pbx.read_text()
    if 'com.apple.InAppPurchase' not in project:
        project = project.replace('\\t\\t\\t\\t\\tLastSwiftMigration = 1100;\\n\\t\\t\\t\\t\\tProvisioningStyle = Automatic;', '\\t\\t\\t\\t\\tLastSwiftMigration = 1100;\\n\\t\\t\\t\\t\\tProvisioningStyle = Automatic;\\n\\t\\t\\t\\t\\tSystemCapabilities = {\\n\\t\\t\\t\\t\\t\\tcom.apple.InAppPurchase = {\\n\\t\\t\\t\\t\\t\\t\\tenabled = 1;\\n\\t\\t\\t\\t\\t\\t};\\n\\t\\t\\t\\t\\t};')
        pbx.write_text(project)
    def insert_after_dict(key_block: str):
        nonlocal text
        if key_block.split('</string>')[0] in text:
            return
        text = text.replace('<dict>', '<dict>\n' + key_block, 1)
    insert_after_dict('  <key>GADApplicationIdentifier</key>\n  <string>' + IOS_APP_ID + '</string>\n')
    insert_after_dict('  <key>NSUserTrackingUsageDescription</key>\n  <string>SleepRise, size uygun reklamları göstermek ve reklam performansını ölçmek için izin ister.</string>\n')
    if '<key>SKAdNetworkItems</key>' not in text:
        text = text.replace('</dict>', '  <key>SKAdNetworkItems</key>\n  <array>\n    <dict><key>SKAdNetworkIdentifier</key><string>cstr6suwn9.skadnetwork</string></dict>\n  </array>\n</dict>', 1)
    INFO_PLIST_PATH.write_text(text)


html = upsert_html(HTML_PATH.read_text())
HTML_PATH.write_text(html)
upsert_android()
upsert_main_activity()
upsert_ios()
print('SleepRise AdMob v51 patch applied')
print('Android app:', ANDROID_APP_ID)
print('Android banner:', ANDROID_BANNER_ID)
print('Android rewarded:', ANDROID_REWARDED_ID)
print('iOS app:', IOS_APP_ID)
print('iOS banner:', IOS_BANNER_ID)
print('iOS rewarded:', IOS_REWARDED_ID)
