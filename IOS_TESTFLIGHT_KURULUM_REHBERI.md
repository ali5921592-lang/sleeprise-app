# SleepRise iOS → TestFlight Otomasyon Rehberi

Bu proje artık GitHub’a gönderilen güncellemeleri **iOS için imzalayıp `.ipa` dosyasına dönüştürebilecek** ve tercih edildiğinde bu dosyayı **TestFlight** üzerinden App Store Connect hesabına gönderebilecek bir iş akışı içerir. İş akışı, derlemeyi macOS üzerinde yapar; bu nedenle iOS uygulaması için gereken Xcode ortamı GitHub’ın geçici macOS çalıştırıcısında sağlanır.

> **Önemli:** Bu otomasyon TestFlight’a build gönderir. App Store’da herkese açık yayın için App Store Connect içindeki ürün sayfası, gizlilik bilgileri, ekran görüntüleri ve Apple inceleme gönderimi ayrıca tamamlanmalıdır.

## 1. Önce Apple tarafını hazırlayın

Apple Developer hesabınızda SleepRise için benzersiz bir App ID / Bundle ID oluşturun. Bu değer, depoda kullanılan kimlikle ve App Store Connect’te açacağınız uygulama kaydıyla birebir aynı olmalıdır. Projedeki varsayılan kimlik `com.sleepify.app` şeklindedir. Eğer Apple tarafında farklı bir kimlik, örneğin `com.sirketiniz.sleeprise`, oluşturursanız önce `capacitor.config.json` içindeki `appId` değerini buna değiştirin, sonra `pnpm sync:ios` çalıştırıp güncellenen `ios/` klasörünü depoya gönderin.

Ardından App Store Connect’te aynı Bundle ID ile SleepRise uygulama kaydını açın. Uygulama kaydı açılmadan gönderilen IPA dosyası TestFlight’a bağlanamaz.

| Apple tarafındaki gereksinim | Amaç |
|---|---|
| Apple Developer Program üyeliği | Uygulamayı imzalamak ve TestFlight dağıtımı yapmak |
| Benzersiz Bundle ID | iOS uygulaması ile App Store Connect kaydını eşleştirmek |
| iOS Distribution sertifikası | Release IPA dosyasını imzalamak |
| App Store provisioning profile | Sertifika, takım ve Bundle ID eşleşmesini tanımlamak |
| App Store Connect API anahtarı | GitHub’ın TestFlight’a güvenli yükleme yapmasını sağlamak |

Apple’ın güncel yükleme eylemi, API anahtarının **App Manager** rolüyle oluşturulmasını ve özel `.p8` anahtar dosyasının güvenli olarak saklanmasını önerir.[1]

## 2. GitHub değişkenlerini ve gizli anahtarları girin

GitHub deposunda **Settings → Secrets and variables → Actions** sayfasını açın. Aşağıdaki değerleri ekleyin. Anahtar, sertifika, profil veya parola değerlerini hiçbir zaman kod dosyasına, README’ye ya da commit mesajına yazmayın.

| Tür | Ad | Değer |
|---|---|---|
| Variable | `IOS_CI_ENABLED` | İlk testten sonra `true`; varsayılan olarak boş/`false` bırakın |
| Variable | `IOS_AUTO_UPLOAD` | Ana dala her gönderimde TestFlight yüklemesi için `true`; yalnızca manuel yükleme için `false` |
| Variable | `APPLE_TEAM_ID` | Apple Developer Team ID |
| Variable | `IOS_BUNDLE_ID` | Apple tarafında oluşturduğunuz kesin Bundle ID |
| Variable | `APPSTORE_ISSUER_ID` | App Store Connect API issuer ID |
| Variable | `APPSTORE_API_KEY_ID` | App Store Connect API key ID |
| Variable | `IOS_USES_NON_EXEMPT_ENCRYPTION` | Uygun durumlarda `false`; Apple’ın dışa aktarma uyumluluk sorusuna göre gerekirse `true` |
| Secret | `APPSTORE_API_PRIVATE_KEY` | API anahtarı oluşturulurken bir kez indirilen `AuthKey_*.p8` dosyasının tam içeriği |
| Secret | `APPSTORE_CERTIFICATES_FILE_BASE64` | iOS Distribution `.p12` dosyasının Base64 metni |
| Secret | `APPSTORE_CERTIFICATES_PASSWORD` | `.p12` dosyasını dışa aktarırken belirlediğiniz parola |
| Secret | `APPSTORE_PROVISIONING_PROFILE_BASE64` | App Store provisioning profile `.mobileprovision` dosyasının Base64 metni |

Apple’ın kod imzalama örneği, dağıtım sertifikasının `.p12` olarak dışa aktarıldıktan sonra Base64 biçiminde gizli değişken olarak saklanmasını ve bu sertifikanın iş akışında geçici anahtarlığa aktarılmasını gösterir.[2]

## 3. Base64 değerlerini oluşturun

Mac üzerinde Terminal açın. Aşağıdaki komutlar, her dosya için tek satırlık Base64 metni üretir. Çıktının tamamını ilgili GitHub **Secret** alanına yapıştırın.

```bash
base64 -i ios_distribution.p12 | pbcopy
base64 -i SleepRise_AppStore.mobileprovision | pbcopy
```

İlk komutun çıktısı `APPSTORE_CERTIFICATES_FILE_BASE64`, ikinci komutun çıktısı `APPSTORE_PROVISIONING_PROFILE_BASE64` alanına girilir. Windows veya Linux kullanıyorsanız Base64 çıktısını tek satır hâline getirip aynı alanlara ekleyin. `.p12`, `.mobileprovision` ve `.p8` dosyalarını depoya yüklemeyin.

## 4. İş akışını çalıştırın

Yapılandırma tamamlandıktan sonra depoyu GitHub’a gönderin. Ardından GitHub’daki **Actions** alanından **Build SleepRise iOS and TestFlight** iş akışını açın ve **Run workflow** ile manuel başlatın. İlk denemede TestFlight’a gönderim seçeneğini açık bırakabilirsiniz. İş akışı şu sırayla çalışır: web varlıklarını iOS projesine kopyalar, sertifikayı geçici anahtarlığa aktarır, provisioning profile’ı kurar, Xcode arşivi üretir, imzalı `.ipa` dosyasını oluşturur, çıktıyı iş akışı dosyası olarak saklar ve TestFlight’a gönderir.

Başarılı bir derlemede GitHub Actions çalıştırma sayfasındaki **Artifacts** bölümünde `.ipa` dosyası görünür. TestFlight işlenmesi Apple tarafında tamamlandıktan sonra App Store Connect → TestFlight bölümünde build görünür. Apple’ın resmi GitHub eylemi, IPA yolunu ve App Store Connect API değerlerini kullanarak doğrudan TestFlight yüklemesi yapar.[1]

## 5. Güvenli yayın davranışı

İş akışı, yanlışlıkla yayın yapılmasını önlemek amacıyla `IOS_CI_ENABLED` değeri **tam olarak `true`** değilse hiç çalışmaz. TestFlight’a otomatik gönderim ise iki farklı yolla yapılır: GitHub ana dalına yapılan her gönderimde yalnızca `IOS_AUTO_UPLOAD=true` iken çalışır; manuel başlatmada ise “TestFlight’a yükle” seçeneği etkinse çalışır. Böylece önce yalnızca IPA üretip indirmek, ardından TestFlight otomasyonunu açmak mümkündür.

> **Tavsiye edilen ilk çalıştırma:** Önce `IOS_CI_ENABLED=true` ve `IOS_AUTO_UPLOAD=false` yapın. İş akışını manuel çalıştırın; imzalı IPA artifact olarak başarıyla oluştuğunu görün. Sonra aynı iş akışını manuel TestFlight yüklemesiyle deneyin. Her şey doğru çalıştığında isterseniz `IOS_AUTO_UPLOAD=true` yaparak ana dala her güncelleme gönderdiğinizde otomatik TestFlight yüklemesini açın.

## 6. Mikrofon ve kamera izinleri

iOS projesine mikrofon ve kamera kullanım açıklamaları eklendi. Bu nedenle SleepRise ilk kez uyku ortamı analizini veya ilgili kamera özelliğini kullanmak istediğinde iPhone, kullanıcıya sistem izin penceresi gösterir. Mikrofon metni, ses kaydının saklanmadığını ve analizin cihaz üzerinde yapıldığını açıklar. App Store Connect’teki gizlilik beyanınızın uygulamanın gerçek veri davranışıyla uyumlu olması gerekir.

## Kaynaklar

[1] [Apple-Actions — upload-testflight-build](https://github.com/Apple-Actions/upload-testflight-build)

[2] [Apple-Actions — import-codesign-certs](https://github.com/Apple-Actions/import-codesign-certs)
