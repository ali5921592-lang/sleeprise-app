from pathlib import Path
import re

HTML = Path('/home/ubuntu/sleepify-apk-github/www/index.html')
STYLE_MARKER = '<style id="sleeprise-subscription-v52-style">'
SCRIPT_MARKER = '<script id="sleeprise-subscription-v52">'

STYLE = r'''<style id="sleeprise-subscription-v52-style">
.sr-pro-sheet{position:fixed;inset:0;z-index:12000;display:none;align-items:flex-end;justify-content:center;background:rgba(5,13,31,.48);backdrop-filter:blur(8px);padding:18px}.sr-pro-sheet.on{display:flex}.sr-pro-panel{width:min(520px,100%);max-height:min(86vh,720px);overflow:auto;border-radius:26px 26px 18px 18px;background:var(--surface,#fff);color:var(--ink,#10233f);box-shadow:0 26px 70px rgba(3,13,34,.35);padding:20px}.sr-pro-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}.sr-pro-head b{font-size:20px;letter-spacing:-.035em}.sr-pro-head p{margin:6px 0 0;color:var(--muted,#6f7f96);font-size:11px;line-height:1.45}.sr-pro-close{width:32px;height:32px;border:1px solid var(--line,#dce5f1);border-radius:50%;background:transparent;color:var(--ink,#10233f);font-size:20px;cursor:pointer}.sr-pro-products{display:grid;gap:10px;margin:18px 0}.sr-pro-product{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px;border:1px solid var(--line,#dce5f1);border-radius:17px;background:var(--surface2,#f5f8fc)}.sr-pro-product b{display:block;font-size:13px}.sr-pro-product small{display:block;margin-top:3px;color:var(--muted,#6f7f96);font-size:10px}.sr-pro-product button,.sr-pro-actions button{border:0;border-radius:11px;padding:10px 12px;background:#00a98e;color:#fff;font:800 11px/1 Inter,system-ui,sans-serif;cursor:pointer;white-space:nowrap}.sr-pro-product button:disabled{opacity:.55;cursor:wait}.sr-pro-actions{display:flex;gap:8px;flex-wrap:wrap}.sr-pro-actions button.secondary{background:transparent;color:var(--ink,#10233f);border:1px solid var(--line,#dce5f1)}.sr-pro-foot{margin-top:14px;color:var(--muted,#6f7f96);font-size:10px;line-height:1.45}.app.nightmode .sr-pro-panel{background:#171532;color:#f4f5ff}.app.nightmode .sr-pro-product{background:#211e47;border-color:rgba(255,255,255,.12)}.app.nightmode .sr-pro-head p,.app.nightmode .sr-pro-product small,.app.nightmode .sr-pro-foot{color:#bfc5dd}.app.nightmode .sr-pro-close,.app.nightmode .sr-pro-actions button.secondary{color:#f4f5ff;border-color:rgba(255,255,255,.16)}
@media(prefers-reduced-motion:reduce){.sr-pro-sheet,.sr-pro-panel{animation:none!important;transition:none!important}}
</style>'''

SCRIPT = r'''<script id="sleeprise-subscription-v52">
(function(){
  'use strict';
  const CONFIG=Object.freeze({
    monthly:{id:'com.sleepify.app.pro.monthly',plan:'monthly'},
    yearly:{id:'com.sleepify.app.pro.yearly',plan:'yearly'},
    entitlement:'sleeprise_pro_active',source:'sleeprise_pro_source',product:'sleeprise_pro_product'
  });
  const q=s=>document.querySelector(s), native=()=>!!(window.Capacitor&&typeof window.Capacitor.isNativePlatform==='function'&&window.Capacitor.isNativePlatform());
  const api=()=>window.Capacitor?.Plugins?.NativePurchases||null;
  const langCode=()=>{const raw=(document.documentElement.lang||'').slice(0,2).toLowerCase();return raw||'en'};
  const TX={tr:{title:'SleepRise Pro',sub:'Reklamları kaldır ve uygulamanın sakin akışını koru.',month:'Aylık Pro',year:'Yıllık Pro',yearNote:'Daha avantajlı yıllık seçenek',buy:'Abone ol',restore:'Satın alımları geri yükle',manage:'Aboneliği yönet',close:'Kapat',loading:'Mağaza fiyatları yükleniyor…',notReady:'Mağaza ürünleri henüz hazır değil. Google Play Console ve App Store Connect’te ürünleri oluşturduktan sonra tekrar dene.',success:'SleepRise Pro etkin. Reklamlar kaldırıldı.',cancel:'Satın alma iptal edildi.',error:'Satın alma tamamlanamadı. Lütfen tekrar dene.',footer:'Fiyat ve para birimi mağaza tarafından belirlenir; uygulama sabit fiyat dayatmaz.'},en:{title:'SleepRise Pro',sub:'Remove ads and keep the calm flow of the app.',month:'Monthly Pro',year:'Yearly Pro',yearNote:'Better annual value',buy:'Subscribe',restore:'Restore purchases',manage:'Manage subscription',close:'Close',loading:'Loading store prices…',notReady:'Store products are not ready yet. Create them in Google Play Console and App Store Connect, then try again.',success:'SleepRise Pro is active. Ads are removed.',cancel:'Purchase cancelled.',error:'The purchase could not be completed. Please try again.',footer:'Price and currency are supplied by the store; the app does not force a fixed price.'},es:{title:'SleepRise Pro',sub:'Elimina los anuncios y conserva una experiencia tranquila.',month:'Pro mensual',year:'Pro anual',yearNote:'Mejor valor anual',buy:'Suscribirse',restore:'Restaurar compras',manage:'Gestionar suscripción',close:'Cerrar',loading:'Cargando precios de la tienda…',notReady:'Los productos aún no están listos. Créelos en Google Play Console y App Store Connect y vuelva a intentarlo.',success:'SleepRise Pro está activo. Los anuncios se han eliminado.',cancel:'Compra cancelada.',error:'No se pudo completar la compra. Inténtalo de nuevo.',footer:'La tienda proporciona el precio y la moneda; la aplicación no impone un precio fijo.'},de:{title:'SleepRise Pro',sub:'Entferne Anzeigen und bewahre den ruhigen Ablauf.',month:'Pro monatlich',year:'Pro jährlich',yearNote:'Besserer Jahreswert',buy:'Abonnieren',restore:'Käufe wiederherstellen',manage:'Abo verwalten',close:'Schließen',loading:'Store-Preise werden geladen…',notReady:'Store-Produkte sind noch nicht bereit. Erstelle sie in Google Play Console und App Store Connect und versuche es erneut.',success:'SleepRise Pro ist aktiv. Anzeigen wurden entfernt.',cancel:'Kauf abgebrochen.',error:'Der Kauf konnte nicht abgeschlossen werden. Bitte versuche es erneut.',footer:'Preis und Währung kommen aus dem Store; die App erzwingt keinen festen Preis.'},fr:{title:'SleepRise Pro',sub:'Supprimez les annonces et gardez un parcours apaisant.',month:'Pro mensuel',year:'Pro annuel',yearNote:'Meilleure valeur annuelle',buy:'S’abonner',restore:'Restaurer les achats',manage:'Gérer l’abonnement',close:'Fermer',loading:'Chargement des prix…',notReady:'Les produits ne sont pas encore prêts. Créez-les dans Google Play Console et App Store Connect, puis réessayez.',success:'SleepRise Pro est actif. Les annonces sont supprimées.',cancel:'Achat annulé.',error:'Achat impossible. Veuillez réessayer.',footer:'Le prix et la devise sont fournis par la boutique ; l’application n’impose pas de prix fixe.'},pt:{title:'SleepRise Pro',sub:'Remova os anúncios e mantenha o fluxo tranquilo do app.',month:'Pro mensal',year:'Pro anual',yearNote:'Melhor valor anual',buy:'Assinar',restore:'Restaurar compras',manage:'Gerenciar assinatura',close:'Fechar',loading:'Carregando preços da loja…',notReady:'Os produtos ainda não estão prontos. Crie-os no Google Play Console e App Store Connect e tente novamente.',success:'SleepRise Pro está ativo. Os anúncios foram removidos.',cancel:'Compra cancelada.',error:'Não foi possível concluir a compra. Tente novamente.',footer:'O preço e a moeda são fornecidos pela loja; o app não impõe um preço fixo.'},ar:{title:'SleepRise Pro',sub:'أزل الإعلانات وحافظ على تجربة التطبيق الهادئة.',month:'Pro شهري',year:'Pro سنوي',yearNote:'قيمة سنوية أفضل',buy:'اشترك',restore:'استعادة المشتريات',manage:'إدارة الاشتراك',close:'إغلاق',loading:'جارٍ تحميل أسعار المتجر…',notReady:'منتجات المتجر غير جاهزة بعد. أنشئها في Google Play Console وApp Store Connect ثم حاول مرة أخرى.',success:'SleepRise Pro نشط. تمت إزالة الإعلانات.',cancel:'تم إلغاء الشراء.',error:'تعذر إتمام الشراء. حاول مرة أخرى.',footer:'المتجر يحدد السعر والعملة؛ التطبيق لا يفرض سعراً ثابتاً.'},zh:{title:'SleepRise Pro',sub:'移除广告，保持安静的使用体验。',month:'Pro 月度',year:'Pro 年度',yearNote:'年度方案更划算',buy:'订阅',restore:'恢复购买',manage:'管理订阅',close:'关闭',loading:'正在加载商店价格…',notReady:'商店商品尚未准备好。请在 Google Play Console 和 App Store Connect 中创建商品后重试。',success:'SleepRise Pro 已启用，广告已移除。',cancel:'已取消购买。',error:'购买未完成，请重试。',footer:'价格和货币由商店提供；应用不会强制固定价格。'},ja:{title:'SleepRise Pro',sub:'広告を削除し、落ち着いた体験を保ちます。',month:'Pro 月額',year:'Pro 年額',yearNote:'年間プランがお得',buy:'登録する',restore:'購入を復元',manage:'サブスクリプションを管理',close:'閉じる',loading:'ストア価格を読み込み中…',notReady:'ストア商品がまだ準備されていません。Google Play Console と App Store Connect で商品を作成してから再試行してください。',success:'SleepRise Pro が有効になり、広告が削除されました。',cancel:'購入をキャンセルしました。',error:'購入を完了できませんでした。もう一度お試しください。',footer:'価格と通貨はストアが提供します。アプリが固定価格を強制することはありません。'}};
  const t=k=>(TX[langCode()]||TX.en)[k]||TX.en[k]||k;
  let products=[],busy=false,ready=false;
  function list(){return [CONFIG.monthly.id,CONFIG.yearly.id]}
  function setPro(active,product){try{if(active){localStorage.setItem(CONFIG.entitlement,'1');localStorage.setItem(CONFIG.source,'native');if(product)localStorage.setItem(CONFIG.product,product)}else{localStorage.removeItem(CONFIG.entitlement);localStorage.removeItem(CONFIG.source);localStorage.removeItem(CONFIG.product)}}catch(e){};window.dispatchEvent(new CustomEvent('sleeprise-pro-changed',{detail:{active}}));}
  function isPro(){return localStorage.getItem(CONFIG.entitlement)==='1'&&localStorage.getItem(CONFIG.source)==='native'}
  function msg(text){try{if(typeof notice==='function')return notice(text);if(typeof toast==='function')return toast(text);console.info(text)}catch(e){}}
  function productFor(id){return products.find(p=>p.identifier===id||p.planIdentifier===id)}
  function productText(p,key){if(!p)return t(key);return p.priceString?`${t(key)} · ${p.priceString}`:t(key)}
  function render(){
    const sheet=q('#srProSheet');if(!sheet)return;
    const listEl=sheet.querySelector('[data-sr-products]');
    if(isPro()){listEl.innerHTML='<div class="sr-pro-product"><div><b>'+t('title')+'</b><small>'+t('success')+'</small></div></div>';sheet.querySelector('[data-sr-restore]').style.display='none';return}
    if(!native()||!ready){listEl.innerHTML='<div class="sr-pro-product"><div><b>'+t('title')+'</b><small>'+t('notReady')+'</small></div></div>';}
    else if(!products.length){listEl.innerHTML='<div class="sr-pro-product"><div><b>'+t('title')+'</b><small>'+t('notReady')+'</small></div></div>';}
    else{listEl.innerHTML=[['monthly',CONFIG.monthly.id,'month'],['yearly',CONFIG.yearly.id,'year']].map(([kind,id,label])=>{const p=productFor(id);const note=label==='year'?'<small>'+t('yearNote')+'</small>':'';return '<div class="sr-pro-product"><div><b>'+productText(p,label)+'</b>'+note+'</div><button type="button" data-sr-pro-buy="'+id+'" '+(busy?'disabled':'')+'>'+t('buy')+'</button></div>'}).join('')}
    sheet.querySelector('[data-sr-restore]').textContent=t('restore');sheet.querySelector('[data-sr-manage]').textContent=t('manage');sheet.querySelector('[data-sr-close]').textContent=t('close');sheet.querySelector('[data-sr-foot]').textContent=t('footer');
  }
  function ensureSheet(){
    if(q('#srProSheet'))return;
    const sheet=document.createElement('div');sheet.id='srProSheet';sheet.className='sr-pro-sheet';sheet.setAttribute('role','dialog');sheet.setAttribute('aria-modal','true');
    sheet.innerHTML='<div class="sr-pro-panel"><div class="sr-pro-head"><div><b>'+t('title')+'</b><p>'+t('sub')+'</p></div><button type="button" class="sr-pro-close" data-sr-pro-close aria-label="'+t('close')+'">×</button></div><div class="sr-pro-products" data-sr-products></div><div class="sr-pro-actions"><button type="button" class="secondary" data-sr-restore>'+t('restore')+'</button><button type="button" class="secondary" data-sr-manage>'+t('manage')+'</button></div><div class="sr-pro-foot" data-sr-foot>'+t('footer')+'</div></div>';
    document.body.appendChild(sheet);
    sheet.addEventListener('click',ev=>{if(ev.target===sheet||ev.target.closest('[data-sr-pro-close]'))sheet.classList.remove('on')});
    sheet.addEventListener('click',ev=>{const buy=ev.target.closest('[data-sr-pro-buy]');if(buy)buyProduct(buy.dataset.srProBuy);if(ev.target.closest('[data-sr-restore]'))restore();if(ev.target.closest('[data-sr-manage]'))manage()});
  }
  function open(){ensureSheet();render();q('#srProSheet')?.classList.add('on');loadProducts().then(render).catch(()=>render())}
  async function loadProducts(){
    if(!native()){ready=false;products=[];return products}
    const p=api();if(!p||!p.getProducts){ready=false;products=[];return products}
    try{const support=await p.isBillingSupported?.();if(support&&support.isBillingSupported===false){ready=false;products=[];return products}const result=await p.getProducts({productIdentifiers:list(),productType:'subs'});products=result?.products||[];ready=products.length>0;return products}catch(e){console.warn('SleepRise products',e);ready=false;products=[];return products}
  }
  async function buyProduct(id){
    if(busy)return;const p=api();if(!native()||!p?.purchaseProduct){msg(t('notReady'));return}
    busy=true;render();
    try{const meta=productFor(id)||{};const plan=meta.planIdentifier||((id===CONFIG.monthly.id)?CONFIG.monthly.plan:CONFIG.yearly.plan);const tr=await p.purchaseProduct({productIdentifier:id,planIdentifier:plan,productType:'subs',quantity:1,autoAcknowledgePurchases:true});if(tr){setPro(true,id);msg(t('success'));q('#srProSheet')?.classList.remove('on')}}catch(e){const text=String(e?.message||e||'');msg(/cancel/i.test(text)?t('cancel'):t('error'));console.warn('SleepRise purchase',e)}finally{busy=false;render()}
  }
  async function restore(){
    const p=api();if(!native()||!p){msg(t('notReady'));return}
    try{await p.restorePurchases?.();const out=await p.getPurchases?.({productType:'subs'});const found=(out?.purchases||[]).find(x=>list().includes(x.productIdentifier));if(found){setPro(true,found.productIdentifier);msg(t('success'))}else{setPro(false);msg(t('notReady'))}render()}catch(e){console.warn('SleepRise restore',e);msg(t('error'))}
  }
  async function manage(){const p=api();if(!native()||!p?.manageSubscriptions){msg(t('notReady'));return}try{await p.manageSubscriptions()}catch(e){console.warn('SleepRise manage',e)}}
  async function refresh(){ensureSheet();if(native())await restore();render()}
  window.SleepRiseSubscription={isPro,open,loadProducts,buyProduct,restore,manage,refresh,products:()=>products,config:CONFIG};
  function start(){ensureSheet();setTimeout(()=>{loadProducts().then(render).catch(()=>render())},900)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
</script>'''

s = HTML.read_text()
s = re.sub(r'<style id="sleeprise-subscription-v52-style">.*?</style>', '', s, flags=re.S)
s = re.sub(r'<script id="sleeprise-subscription-v52">.*?</script>', '', s, flags=re.S)
if '</body>' not in s:
    raise SystemExit('body kapanış etiketi yok')
HTML.write_text(s.replace('</body>', STYLE + '\n' + SCRIPT + '\n</body>', 1))
print('SleepRise subscription v52 patch applied')
print('monthly:', CONFIG['monthly'] if 'CONFIG' in globals() else 'com.sleepify.app.pro.monthly')
print('yearly: com.sleepify.app.pro.yearly; plans: monthly/yearly')
