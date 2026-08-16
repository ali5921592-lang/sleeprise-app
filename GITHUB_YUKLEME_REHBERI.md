# SleepRise v44 — GitHub’a Yükleme Rehberi

Bu paket, GitHub web sayfasındaki **dosya yükleme alanına ZIP olarak yüklenmemelidir**. Ekrandaki hata ZIP dosyasının büyük olmasından kaynaklanıyor. GitHub web arayüzünde tek dosya yükleme sınırı **25 MiB**’dir; komut satırında tek dosya sınırı **100 MiB**’e kadar çıkar. Daha büyük dosyalar için Git LFS gerekir [1]. SleepRise paketindeki MP3 ve MP4 dosyaları tek tek bu sınırın altında olsa da ZIP dosyasının tamamı tek bir dosya gibi değerlendirildiği için web arayüzüyle yüklenemez.

> **Doğru yöntem:** ZIP dosyasını bilgisayarda çıkar, içindeki proje klasörünü GitHub Desktop veya Git komutlarıyla gönder. ZIP dosyasının kendisini GitHub’a gönderme.

## 1. Doğru paketi indir ve çıkar

`SleepRise` projesi için şu paketi kullan:

`/home/ubuntu/sleepify-apk-github-v44-github-upload.zip`

Bu arşiv yaklaşık **83 MB** boyutundadır. Android ve iOS içinde `www/` klasörünün üç kez tutulması nedeniyle oluşan tekrarlı native web çıktıları pakete eklenmemiştir. GitHub Actions, Android ve iOS derlemesinden önce `npx cap sync android` ve `npx cap sync ios` komutlarını çalıştırarak bu dosyaları `www/` klasöründen yeniden oluşturur.

ZIP dosyasını bilgisayarında çıkar. Örneğin Windows’ta masaüstünde şu klasör oluşmalıdır:

```text
C:\SleepRise\
├── www\
├── android\
├── ios\
├── .github\workflows\
├── package.json
├── pnpm-lock.yaml
└── capacitor.config.ts
```

Klasörü ZIP’in içindeki bir başka ZIP olarak bırakma; `package.json` dosyası doğrudan `C:\SleepRise\` klasörünün içinde görünmelidir.

## 2. GitHub’da boş depo oluştur

1. [github.com/new](https://github.com/new) adresini aç.
2. Repository name alanına `sleeprise` veya `sleeprise-app` yaz.
3. Public ya da Private seçimini yap.
4. **Add a README file**, `.gitignore` ve license seçeneklerini bu aşamada işaretleme; depo boş oluşturulsun.
5. **Create repository** düğmesine bas.
6. Açılan sayfada depo adresini kopyala. Adres şu biçimde olur:

```text
https://github.com/KULLANICI_ADIN/sleeprise.git
```

## 3. En kolay yöntem: GitHub Desktop

[GitHub Desktop’ı indir](https://desktop.github.com/download/) ve GitHub hesabınla giriş yap.

1. GitHub Desktop’ı aç.
2. **File → Add local repository** seç.
3. Çıkardığın `C:\SleepRise` klasörünü seç.
4. Klasör Git deposu değilse **create a repository** veya **Create repository** seçeneğini kullanarak yerel depo oluştur.
5. Repository name olarak `sleeprise` yaz; Local path olarak `C:\SleepRise` klasörünü seç.
6. **Create repository** düğmesine bas.
7. Üst bölümde **Publish repository** seçeneğine bas.
8. GitHub depo adını `sleeprise` yap, görünürlük seçimini kontrol et ve **Publish repository** düğmesine bas.
9. İlk gönderim uzun sürebilir; MP3 ve MP4 dosyaları da gönderileceği için işlem bitene kadar GitHub Desktop’ı kapatma.

GitHub Desktop büyük dosyaları Git LFS ile de yönetebilir; ancak bu SleepRise paketinde dosyalar 100 MiB altında olduğu için ilk yüklemede Git LFS zorunlu değildir [2].

## 4. Windows’ta komut satırı yöntemi

GitHub Desktop kullanmak istemezsen [Git for Windows’ı indir](https://git-scm.com/download/win), ardından **Git Bash** aç. Aşağıdaki komutlarda `KULLANICI_ADIN` bölümünü kendi GitHub kullanıcı adınla değiştir:

```bash
cd /c/SleepRise
git init -b main
git add .
git commit -m "SleepRise v44 uygulamasını ekle"
git remote add origin https://github.com/KULLANICI_ADIN/sleeprise.git
git push -u origin main
```

GitHub kullanıcı adı ve parola sorulursa parola yerine GitHub hesabında oluşturulmuş Personal Access Token kullanılır. Daha kolay yol, GitHub Desktop’ın oturum açma özelliğidir.

Eğer `remote origin already exists` hatası alırsan şu komutları kullan:

```bash
git remote set-url origin https://github.com/KULLANICI_ADIN/sleeprise.git
git push -u origin main
```

Eğer `rejected` veya `non-fast-forward` hatası alırsan GitHub deposunu README ile başlatmış olabilirsin. En kolay çözüm boş bir GitHub deposu oluşturup komutları o yeni adrese uygulamaktır.

## 5. GitHub web arayüzü neden önerilmiyor?

Web arayüzünde ZIP dosyasını yüklemeye çalışma; ekrandaki hatanın sebebi budur. İstersen ZIP’i çıkarıp yalnızca küçük dosyaları **Add file → Upload files** ile yükleyebilirsin, fakat web arayüzünde aynı anda en fazla 100 dosya seçilebilir ve tek dosya 25 MiB’yi geçemez [1]. SleepRise’ın ses ve video klasörleri bulunduğu için bu yöntem gereksiz derecede zahmetlidir. GitHub Desktop veya Git Bash kullanmak daha doğru ve güvenilirdir.

## 6. Git LFS ne zaman gerekir?

Normal Git gönderiminde tek dosya 100 MiB’yi geçerse Git LFS gerekir. SleepRise’ın mevcut MP3 ve MP4 dosyalarının her biri bu değerin altında olduğundan önce normal GitHub Desktop yöntemini dene. Yine de GitHub büyük dosya uyarısı verirse Git LFS kur:

```bash
git lfs install
git lfs track "www/audio/*.mp3"
git lfs track "www/videos/**/*.mp4"
git add .gitattributes
git add .
git commit -m "Ses ve video dosyalarını Git LFS ile yönet"
git push -u origin main
```

Git LFS depoda gerçek büyük dosya yerine işaretçi dosyaları tutar ve dosyaları klonlama sırasında indirir [2]. GitHub Free hesaplarında Git LFS tek dosya üst sınırı 2 GB’tır [2]. LFS kullanırsan hesabındaki Git LFS depolama ve bant genişliği kotasını da kontrol et.

## 7. GitHub Actions ile APK derleme

Yükleme tamamlandıktan sonra GitHub deposunda **Actions** sekmesine gir. Android iş akışını çalıştırmak için `build-android-apk.yml` dosyasındaki workflow’u seçip **Run workflow** düğmesine bas. Workflow önce bağımlılıkları kurar, sonra `npx cap sync android` ile `www/` içindeki SleepRise dosyalarını Android projesine kopyalar ve APK’yı üretir.

APK tamamlandığında ilgili Actions çalışmasının **Artifacts** bölümünden APK’yı indirebilirsin. iOS TestFlight iş akışı için Apple sertifikaları, provisioning profile, App Store Connect API anahtarı ve ilgili GitHub Secrets değerleri ayrıca tanımlanmalıdır; bunun rehberi `IOS_TESTFLIGHT_KURULUM_REHBERI.md` dosyasındadır.

## Kısa çözüm

Senin durumda uygulanacak sıra şudur:

```text
1. sleepify-apk-github-v44-github-upload.zip dosyasını indir.
2. ZIP’i C:\SleepRise klasörüne çıkar.
3. github.com/new adresinde boş bir repo oluştur.
4. GitHub Desktop → Add local repository → C:\SleepRise.
5. Publish repository.
6. GitHub → Actions → build-android-apk.yml → Run workflow.
```

### Kaynaklar

[1]: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository "GitHub Docs — Adding a file to a repository"

[2]: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage "GitHub Docs — About Git Large File Storage"
