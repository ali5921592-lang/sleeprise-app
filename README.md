# Sleepify — GitHub’dan Android APK Derleme Paketi

Bu depo, Sleepify uygulamasını **tek HTML uygulaması + Capacitor Android kabuğu** olarak APK’ye dönüştürür. GitHub Actions her `main` dalı gönderiminde ve manuel çalıştırmada debug APK oluşturur.

## Bu pakette neler hazır?

| Bileşen | Konum | Amaç |
| --- | --- | --- |
| Uygulama | `www/index.html` | Sleepify v39; mikrofon hatasını doğru tanılar. |
| Android uygulama kabuğu | `android/` | Capacitor ile oluşturulmuş gerçek Android projesi. |
| Mikrofon/kamera köprüsü | `android/app/src/main/java/com/sleepify/app/MainActivity.java` | WebView `getUserMedia()` isteklerini Android izinleriyle bağlar. |
| Android izinleri | `android/app/src/main/AndroidManifest.xml` | `RECORD_AUDIO`, `CAMERA`, `MODIFY_AUDIO_SETTINGS` ve `INTERNET`. |
| APK otomasyonu | `.github/workflows/build-android-apk.yml` | GitHub Actions üzerinden debug APK üretir. |

## GitHub’a yükleme

1. GitHub’da boş bir depo oluştur. Önerilen isim: `sleepify-apk`.
2. Bu ZIP’in **içindeki dosyaları** deponun kök dizinine yükle. Ek bir klasör katmanı oluşmamasına dikkat et.
3. Deponun varsayılan dalını `main` olarak bırak.
4. Dosyaları yükledikten sonra GitHub’da **Actions** sekmesini aç.
5. **Build Sleepify Android APK** iş akışını seç ve **Run workflow** düğmesine dokun.
6. İş akışı tamamlanınca aynı çalıştırmanın altındaki **Artifacts** bölümünden `sleepify-debug-apk` dosyasını indir.
7. İnen ZIP’i aç; içindeki `app-debug.apk` dosyasını Android telefonuna kur.

> İlk çalıştırma GitHub tarafında Android bağımlılıkları indirildiği için birkaç dakika sürebilir.

## Mikrofon ve kamera neden bu depoda ayrıca yapılandırıldı?

Sleepify’ın uyku analizi, HTML’de `navigator.mediaDevices.getUserMedia()` ile mikrofon ister. Android WebView’de kullanıcı uygulama ayarlarından mikrofon izni vermiş olsa bile WebView bu isteği ayrıca onaylamalıdır. Bu depo üç katmanı birlikte uygular:

1. Android manifest: `RECORD_AUDIO` ve `CAMERA` izinlerini bildirir.
2. Android çalışma zamanı: Kullanıcı izin vermediyse sistem iletişim kutusunu açar.
3. WebView: Yalnızca istenen `AUDIO_CAPTURE` ve `VIDEO_CAPTURE` kaynaklarını HTML’e açar.

Android’in `PermissionRequest` arayüzü, web içeriğinin mikrofon ve kamera gibi korunan kaynaklara erişim isteğini `WebChromeClient.onPermissionRequest` yoluyla iletir; ana uygulama bu isteği açıkça onaylamalı veya reddetmelidir. [1]

## Kurulum sonrası test

| Test | Beklenen sonuç |
| --- | --- |
| Uyku analizi başlatma | Android mikrofon izni ilk kullanımda sorulur; izin sonrası analiz başlar. |
| Kamera kullanan bir özellik | Kamera izni ilk kullanımda sorulur; izin sonrası WebView’e yalnızca kamera kaynağı açılır. |
| Ayarlar → Uygulamalar → Sleepify → İzinler | Mikrofon ve Kamera izinleri listelenir. |
| İzin reddi | Sleepify v39, genel hata yerine APK/WebView yapılandırma açıklaması gösterir. |

## Uygulama HTML’ini güncelleme

Yalnızca `www/index.html` dosyasını değiştir. Sonra GitHub’a gönder. İş akışı `npx cap sync android` komutuyla HTML’i Android projesine kopyalar ve yeni APK üretir.

## Yayın için not

GitHub Actions bu depoda **debug APK** üretir. Google Play’e yüklemek için `assembleRelease` ve imzalama anahtarı gerekir. İmzalama anahtarını depoya yükleme; GitHub Secrets kullan.

## Güvenlik ilkesi

`MainActivity.java`, WebView’in tüm kaynaklarını toptan açmaz. Yalnızca Sleepify tarafından istenen `RESOURCE_AUDIO_CAPTURE` ve `RESOURCE_VIDEO_CAPTURE` kaynaklarını, Android izni verilmişse onaylar. Bu, Android belgelerinin belirli kaynakları açıkça onaylama önerisiyle uyumludur. [1]

## Kaynaklar

[1]: https://developer.android.com/reference/android/webkit/PermissionRequest "Android Developers — PermissionRequest"
[2]: https://developer.android.com/reference/android/Manifest.permission "Android Developers — Manifest.permission"
