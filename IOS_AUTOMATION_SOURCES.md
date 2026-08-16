# iOS Otomasyon Kaynak Notları

GitHub üzerinde çalışan TestFlight yükleme adımı için Apple’ın açık kaynak eylemi kullanılacaktır. Eylem, `.ipa` dosyasını App Store Connect API anahtarıyla yükler. Standart yapılandırma; `APPSTORE_ISSUER_ID` ve `APPSTORE_API_KEY_ID` değerlerini değişken, `APPSTORE_API_PRIVATE_KEY` değerini ise gizli değişken olarak kullanır. Apple’ın örneğinde yükleme eylemi `apple-actions/upload-testflight-build@v5` sürümüyle çalışır.

İmzalama için dağıtım sertifikası, GitHub gizli değişkeninde Base64 kodlu `.p12` dosyası olarak tutulmalıdır. Buna ait parola da ayrı bir gizli değişkendir. Apple’ın sertifika içe aktarma eylemi bu iki değeri `p12-file-base64` ve `p12-password` parametreleriyle macOS anahtarlığına aktarır. İş akışı; yalnızca imzalama bilgileri ve App Store Connect anahtarı mevcutsa TestFlight yüklemesi yapacak şekilde tasarlanacaktır.

Kaynaklar: [Apple-Actions/upload-testflight-build](https://github.com/Apple-Actions/upload-testflight-build) ve [Apple-Actions/import-codesign-certs](https://github.com/Apple-Actions/import-codesign-certs).
