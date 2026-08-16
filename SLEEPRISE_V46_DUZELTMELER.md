# SleepRise v46 Düzeltmeleri

## Video kalitesi

Önceki kısa klipler 480 px genişlikte ve aşırı sıkıştırılmıştı; bu nedenle görüntü bulanık görünüyordu. Videolar orijinal Mixkit kaynaklarından yeniden üretildi. Yeni sürümde klipler yaklaşık 6 saniyelik, sessiz, döngü geçişli ve kaynak yönünü koruyan **720 px genişlikte** H.264 videolardır.

| Kategori | Yeni çözünürlük | Süre | Toplam boyut |
|---|---:|---:|---:|
| Yatay orman/su/gece klipleri | yaklaşık 722 × 406 | yaklaşık 6 saniye | — |
| Dikey kıyı klipleri | 720 × 1280 | yaklaşık 6 saniye | — |
| 7 videonun toplamı | — | — | yaklaşık 9,6 MB |

Sinema Modu video yolları `www/videos` klasöründeki gerçek dosyalarla eşitlendi. Tarayıcı testinde yedi video için `readyState=4`, hata kodu yok ve doğru video boyutları görüldü.

## Alarm sesi düzeltmesi

Ekran görüntüsündeki alarm formu, eski `data-tn` event sistemiyle çalışıyordu. Yeni kartlar yalnızca cleanup katmanının özel `data-sr44-tone` özniteliğini taşıdığı için eski form handler’ı seçimi uygulamıyor ve varsayılan ses çalıyordu. Kartlara `data-tn` özniteliği, DİNLE düğmesine de `data-tn="preview"` eklendi.

Ayrıca `playTone` fonksiyonu 24 gerçek MP3 dosyasını açık bir eşleme tablosuyla kullanacak şekilde düzeltildi. Canlı testte:

| Seçilen kart | Oynatılan dosya |
|---|---|
| Elektronik Buzzer 3 | `audio/electronic-buzzer-3.mp3` |
| Üç Tonlu Siren | `audio/three-tone-siren.mp3` |

İki farklı seçimde kart state’i de doğru biçimde yalnızca seçilen kartta `on` olarak kaldı.

## Paket doğrulaması

Android ve iOS Capacitor web varlıkları yeniden `cap sync` edildi. Her iki native çıktı içinde güncel `index.html`, 31 MP3 dosyası ve 7 yüksek kaliteli video bulunmaktadır. APK/IPA native derlemesi bu sandbox ortamında CocoaPods/Xcode bulunmadığı için alınmadı; GitHub Actions workflow’u derleme öncesi eşitlemeyi çalıştıracak şekilde kullanılabilir.
