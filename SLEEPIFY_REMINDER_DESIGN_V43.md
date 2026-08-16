# SleepRise v43 Hatırlatıcılar Tasarım Kararı

## Bilgi mimarisi

Hatırlatıcılar, Sesler sekmesinden tamamen ayrılır ve alt navigasyonda bağımsız bir sekme olarak görünür. Ekranın üstünde **Tümü**, **İlaç**, **Döngü** ve **Nöbet** filtreleri bulunur. İlk bölümde Bugün, Yaklaşan ve Takip özeti kartları; ikinci bölümde günün zaman çizelgesi; üçüncü bölümde hızlı ekleme kartları; son bölümde modüle göre mini grafik veya takvim yer alır.

## İlaç görünümü

İlaç kartı ilaç adı, doz, saat, sonraki alım ve stok bilgisini gösterir. Kullanıcı tek dokunuşla **Aldım**, **Atladım** veya **Ertele** aksiyonlarından birini seçer. Son yedi güne ait alınan/atlanan dozlar küçük bir uyum grafiğiyle gösterilir. İleri düzey klinik karar, doz önerisi veya etkileşim uyarısı verilmez.

## Döngü görünümü

Döngü kartı yalnızca uygun profil seçildiğinde görünür. Son başlangıç tarihi, döngü günü, tahmini sonraki başlangıç ve son üç döngü için kısa bir karşılaştırma görünümü sunar. Takvimde dönem günleri vurgulanır; semptom chip’leri ile ruh hâli, enerji, ağrı ve uyku notu kaydedilebilir. Sonuçlar kişisel takip tahminidir ve tıbbi tanı/gebelik öngörüsü olarak sunulmaz.

## Nöbet görünümü

Nöbet kartında Gündüz, Akşam, Gece, Eğitim ve Özel şablonları bulunur. Her şablon renk, başlangıç-bitiş saati, konum/not ve vardiya öncesi bildirim dakikasını taşıyabilir. Haftalık görünüm renk kodlu günlerden oluşur; toplam çalışma saati ve gece nöbeti sayısı mini istatistik olarak gösterilir.

## Araştırma dayanakları

İlaç modülü MyTherapy’deki alım günlüğü, atlanan/alınan kayıt, stok/yenileme ve not yaklaşımından esinlenir. Döngü modülü Clue/Flo’da görülen hızlı semptom kaydı, kişisel istatistik ve dönem tahmini mantığını sadeleştirir. Nöbet modülü Supershift/Nursie’deki renkli vardiya şablonları, tekrar ve çalışma saati özeti yaklaşımını alır.

Kaynaklar: [MyTherapy](https://www.mytherapyapp.com/), [Clue](https://helloclue.com/), [Supershift](https://apps.apple.com/us/app/supershift-shift-calendar/id1104165041), [Nursie](https://apps.apple.com/us/app/nursie-nurse-shift-planner/id6538714730).
