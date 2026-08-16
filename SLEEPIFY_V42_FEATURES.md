# SleepRise v42 Özellik Rehberi

## Yeni başlangıç akışı

Uygulama ilk açıldığında mevcut kısa Luma eğitiminden sonra yaş aralığı ve cinsiyet tercihi sorulur. Bu bilgiler yalnızca ekrandaki önerileri sadeleştirmek için kullanılır. Erkek veya “belirtmek istemiyorum” seçildiğinde menstrual döngü kartı gösterilmez; kadın seçildiğinde Planım sekmesinde isteğe bağlı olarak açılır. Profil daha sonra **Sesler → Profil → Profili düzenle** yoluyla değiştirilebilir.

## Sesler sekmesi

Alt navigasyondaki **Sesler** sekmesi, önceki sürümde ekranı uzatan alarm ve rahatlama listelerinin yerine geçer. Alarm sesleri güçlü elektronik, siren, mekanik, pager ve hayvan kategorilerinde filtrelenebilir. Her ses ayrı ayrı dinlenebilir. Rahatlama sesleri yağmur, orman, su/dalga ve gece kategorilerinde filtrelenebilir; Uyku Miksinde yağmur + orman + gece kuşları, Kıyı Miksinde iki dalga kaydı birlikte çalar.

## Radyo ile uyanma

Sesler sekmesindeki **Radyo ile uyan** kartından HTTPS radyo stream URL’si eklenebilir. Kanal adı ve URL kaydedilir; önizleme ve durdurma düğmeleri vardır. **Rastgele İstasyon** düğmesi sağlıklı HTTPS istasyonlarını Radio Browser API’den seçer. Yayıncının akış biçimine ve işletim sistemi kısıtlarına göre arka planda radyo çalma davranışı değişebilir. Uygulama radyo stream’ini kendisi barındırmaz.

## Planım sekmesi

**İlaç**, **Nöbet** veya **Kişisel** türlerinden biri seçilerek başlık, tarih/saat ve günlük tekrar ayarlanabilir. Android Capacitor paketinde yerel bildirim eklentisi bulunur; bildirim izni verildiğinde cihazın işletim sistemi üzerinden bildirim planlanır. Tarayıcı sürümünde uygulama açıkken ekranda hatırlatma gösterilir.

Menstrual takip yalnızca kullanıcının girdiği son başlangıç tarihi ve döngü uzunluğuna göre basit bir sonraki tarih tahmini sunar. Bu özellik tıbbi tanı, doğurganlık tahmini veya sağlık tavsiyesi değildir.

## Teknik not

Android projesine `@capacitor/local-notifications` eklendi ve web varlıkları Capacitor’a eşitlendi. Son APK derlemesi Apple/iOS veya Android SDK kurulu bir CI/macOS/Android ortamında yapılmalıdır. Ses varlıklarının lisans kayıtları `www/audio/AUDIO_LICENSES.md` içinde tutulur.
