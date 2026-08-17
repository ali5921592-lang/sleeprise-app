# SleepRise Monetizasyon Yapılandırması

## Durum

SleepRise için **kademeli AdMob reklam modeli** ve **Pro abonelik native satın alma köprüsü** eklendi. Normal bugün, uyku, uyanış ve alarm akışlarında banner gösterilmez. Banner yalnızca rahatlama/atmosfer/video ekranının altına, içerik alanını kapatmayan güvenli boşlukla eklenir.

AdMob kimlikleri kullanıcı hesabındaki SleepRise Android ve iOS uygulamalarından alınmıştır. Reklam birimi kimlikleri gizli anahtar değildir; ancak uygulamanın mağaza dışı kopyalarında kullanılmamalı ve geliştirme sürümlerinde test reklamı kullanılmalıdır.

| Platform | AdMob uygulama kimliği | Banner birimi | Rewarded birimi |
|---|---|---|---|
| Android | `ca-app-pub-7996356702191225~8756079069` | `ca-app-pub-7996356702191225/8863890276` | `ca-app-pub-7996356702191225/2298481923` |
| iOS | `ca-app-pub-7996356702191225~9135353011` | `ca-app-pub-7996356702191225/3360282152` | `ca-app-pub-7996356702191225/9302873978` |

## Reklam yerleşimi ve kullanıcı deneyimi

| Alan | Uygulanan model | Pro kullanıcı |
|---|---|---|
| Bugün, uyku, uyanış ve alarm | Reklamsız | Reklamsız |
| Rahatla ekranı | Alt merkezde adaptive banner; içerik için 72 px güvenli alt boşluk | Banner kaldırılır |
| Atmosfer seçimi | Seçilen atmosferi açmadan önce 1 rewarded reklam | Reklam yok, doğrudan açılır |
| Uyku analizi | Oturumu bitirip analiz isteminde günde en fazla bir kez 3 rewarded reklamlık paket | Reklam yok, doğrudan analiz |
| Rahatlama sesleri | Ses beş dakika çaldıktan sonra devam etmek için 1 rewarded reklam | Beş dakikalık duraklama yok |
| Kullanıcı videosu, mixer sesi ve özel alarm sesi yükleme | Her yükleme işleminden önce 3 rewarded reklam | Reklam yok, doğrudan dosya seçimi |

Ödüllü reklamlar kullanıcı isteğiyle açılır; reklam hazır değilse özellik başarısız biçimde kilitlenmez, kullanıcıya tekrar deneme mesajı gösterilir. Ses ve video yükleme girdileri hiçbir zaman reklamla otomatik başlatılmaz. AdMob consent/UMP ve iOS App Tracking Transparency akışları native tarafta desteklenir.

Geliştirme derlemesinde `BuildConfig.DEBUG` üzerinden AdMob test kimlikleri kullanılır. Release derlemesi gerçek reklam kimliklerini kullanır. AdMob’un test reklamı yönergeleri, geliştirme sırasında canlı reklamlarla test yapılmamasını gerektirir [1].

## Pro abonelik köprüsü

Capacitor 7 uyumlu `@capgo/native-purchases@7.19.3` paketi Android Google Play Billing ve iOS StoreKit 2 için projeye eklendi. Android Billing izni ve iOS Xcode In-App Purchase capability’si yapılandırıldı.

Ürün kimlikleri şunlardır:

| Ürün | Ürün kimliği | Android base plan |
|---|---|---|
| Aylık Pro | `com.sleepify.app.pro.monthly` | `monthly` |
| Yıllık Pro | `com.sleepify.app.pro.yearly` | `yearly` |

Uygulama ürün fiyatını sabit bir metin olarak yazmaz; mağazadan gelen `priceString` ve para birimini gösterir. Bu, iOS ürün ekranlarında mağaza tarafından sağlanan yerel fiyatın kullanılmasını sağlar [2]. `SleepRiseSubscription` katmanı ürünleri yükler, satın alma başlatır, satın alımları geri yükler ve mağaza abonelik yönetim ekranını açar.

### Önerilen başlangıç fiyatı

Piyasadaki karşılaştırılabilir uyku/meditasyon uygulamalarında yaklaşık **$9.99–$16.99 aylık** ve **$69.99–$79.99 yıllık** seviyeleri görülmektedir [3] [4] [5]. Yeni uygulama için daha düşük bir giriş konumlandırması olarak başlangıçta **$4.99/ay** veya **$29.99/yıl** önerilir. Yıllık planın aylık eşdeğeri yaklaşık $2.50 olur; mağazalar ülkeye, vergiye ve döviz dönüşümüne göre yerel fiyatı ayrıca hesaplar.

Bu fiyatlar henüz mağaza ürünlerine yazılmış değildir. Gerçek satış için aynı ürün kimlikleriyle Google Play Console’da aylık/yıllık subscription ve base plan, App Store Connect’te aynı aylık/yıllık auto-renewable subscription ürünleri oluşturulmalıdır. App Store Connect ve Google Play ürünleri oluşturulmadan satın alma ekranı güvenli şekilde “mağaza ürünleri hazır değil” mesajını gösterir; sahte başarı veya yerel depolamayla kalıcı Pro erişimi verilmez.

## Native ve mağaza kurulumu için kalan adımlar

Google Play Console’da uygulamanın internal testing sürümü yayınlanmalı, `com.sleepify.app.pro.monthly` ve `com.sleepify.app.pro.yearly` ürünleri oluşturulmalı, base plan kimlikleri sırasıyla `monthly` ve `yearly` yapılmalı ve lisans test kullanıcıları eklenmelidir. App Store Connect’te bir subscription group oluşturulmalı, aynı iki product ID eklenmeli, fiyat bölgeleri ve vergi bilgileri tamamlanmalı, Xcode capability’si doğrulanmalı ve Sandbox tester ile denenmelidir.

Üretim uygulamasında satın alma token’larının yalnızca cihazdaki localStorage işaretine güvenmeden backend’de doğrulanması önerilir. Native purchases plugin’i Android purchase token ve iOS receipt/JWS bilgilerini sağlayabilir; sunucu tarafı Google Play Developer API ve App Store Server API doğrulaması sonradan eklenmelidir [6].

## Doğrulama

`check_sleeprise_v49.py` ile 21 inline JavaScript bloğu ve önceki v49/v50 bütünlüğü kontrol edildi; inline JavaScript syntax hatası bulunmadı. Monetizasyon doğrulama betiği AdMob katmanlarının tekil olduğunu, tüm Android/iOS app ve ad unit kimliklerinin, Billing izninin, iOS capability’sinin, ürün kimliklerinin ve Capacitor plugin kayıtlarının mevcut olduğunu doğruladı. Capacitor Android/iOS sync başarılıdır. Bu sandbox’ta Android SDK ve Xcode bulunmadığı için yerel APK/IPA derlemesi çalıştırılamadı; derleme GitHub Actions veya macOS CI üzerinde yapılmalıdır.

> **Önemli:** Bu yapılandırma kod ve native köprüyü hazırlar. Gerçek ücret tahsilatı ancak Google Play Console ve App Store Connect’te ürünler oluşturulup test edilerek mağaza sürümünde çalışır.

## Kaynaklar

[1]: https://developers.google.com/admob/android/test-ads "Google AdMob — Test ads"
[2]: https://github.com/Cap-go/capacitor-native-purchases "Capgo Native Purchases — Capacitor plugin and product API"
[3]: https://www.calm.com/ "Calm — official pricing page"
[4]: https://www.bettersleep.com/blog/headspace-vs-bettersleep-which-app-should-you-pick "BetterSleep — Headspace vs BetterSleep pricing comparison"
[5]: https://www.nytimes.com/wirecutter/reviews/best-meditation-apps/ "Wirecutter — Best meditation apps"
[6]: https://www.revenuecat.com/docs/getting-started/installation/capacitor "RevenueCat — Capacitor installation and purchase infrastructure"
