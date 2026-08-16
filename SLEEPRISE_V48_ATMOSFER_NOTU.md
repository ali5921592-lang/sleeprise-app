# SleepRise v48 — Seçkin Atmosferler

SleepRise Atmosfer ve Sinema Modu, beş seçkin gerçekçi sahneye indirildi. Kullanıcı ayrıca kendi videosunu ekleyebilir; bu nedenle gereksiz sayıda hazır klip tutulmadı.

## Hazır sahneler

| Sahne | Görüntü | Ses |
|---|---|---|
| Şömine | 1280×720, 16 saniye ping-pong döngü | BigSoundBank CC0 şömine çıtırtısı |
| Ateşli yağmur | Şömine görüntüsü üzerine düşük opaklıklı gerçek pencere yağmuru, 1280×720, 16 saniye | Public Domain pencere yağmuru |
| Yağmurlu göl | 1280×720, 16 saniye ping-pong döngü | Public Domain yumuşak yağmur |
| Kar yağan çam | 720×1280 dikey klip, 16 saniye ping-pong döngü | CC0 kış ormanı |
| Karlı çam ormanı | 1280×720, 16 saniye ping-pong döngü | CC0 kış ormanı |

Videolar sessizdir; HTML video katmanı `muted`, `loop` ve `playsinline` olarak çalışır. Atmosfer kartı seçildiğinde ayrı ses katmanı başlar. Bu, video sesinin cihazda iki kez çalmasını ve kullanıcı ses seviyesinin karışmasını önler.

## Lisans

Video kaynakları Mixkit Stock Video Free License altında seçildi ve kaynak sayfaları `ATMOSFER_VIDEO_KAYNAKLARI_V48.md` içinde kaydedildi. Şömine çıtırtısı BigSoundBank Fire, Foley #3322 kaydından alınmış CC0/public-domain equivalent kayıttır; kaynak ve kullanım koşulları `www/audio/AUDIO_LICENSES.md` içinde yer alır.

## Doğrulama

Beş yeni MP4 ve beş poster görseli HTTP 200 ile erişildi. Ateşli yağmur klibi tarayıcıda 16 saniye metadata ve `readyState=4` ile yüklenebilir durumda doğrulandı. Atmosfer kartları doğru başlık, poster, ses ve video yolu ile üretildi. Capacitor Android/iOS eşitlemesi başarıyla tamamlandı.
