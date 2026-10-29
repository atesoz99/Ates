# Hesap widget kurulumu

Bu paket, çalışan uygulamanın HTML ve Swift güncellemesini ve orta boy widget kaynaklarını içerir. Widget, “Bugüne Kadarki Harcama Hedefi” başlığını, ayın gününü, toplam hedefi ve açıklamayı gösterir. Form alanı ve kaydet düğmesi yoktur. Metinler Türkçe/İngilizce uygulama tercihine uyar; renkler uygulamanın karanlık temasındandır. Widget'a dokunmak Hesap'ı açar.

En küçük boyutta tüm metinler mevcut 16/13/24/15 punto boyutlarıyla sığmadığı için yalnızca orta boy sunulmuştur.

## 1. Uygulama dosyalarını güncelle

Önce projenin bir kopyasını yedekle.

1. `finans-ilk-prototip.html` dosyasını projenin aynı adlı dosyasıyla değiştir.
2. `ContentView.swift` dosyasının tamamını paketteki dosyayla değiştir.
3. Mevcut `MyApp.swift`, logo, LaunchScreen ve proje dosyasını koru.

Bu aşamadaki güncelleme, Eurobond silme kontrolünü de içerir. Widget kurulumu tamamlanana kadar ana uygulama çalışmaya devam eder; widget verisi paylaşımı App Groups kurulunca etkinleşir.

## 2. Xcode'da Widget Extension oluştur

1. **File → New → Target** menüsüne gir.
2. iOS altından **Widget Extension** seç.
3. Product Name: **HesapWidget**. Team: mevcut Hesap uygulamasının takımı. **Embed in Application: Hesap** seçili olsun.
4. Live Activity, Control ve Configuration App Intent seçenekleri varsa kapalı bırak. Widget sabit bir görünüm kullanır.
5. Finish'e bas. Şemayı etkinleştirmek sorulursa ana uygulamaya dönmek için Cancel seçebilirsin.
6. Oluşan `HesapWidget` klasöründeki otomatik örnek Swift dosyalarını kaldır. Örnek `WidgetBundle`, `Control` veya `LiveActivity` Swift dosyası varsa onları da kaldır. Widget hedefinde yalnızca bu paketteki **bir** `@main` girişi kalmalıdır.
7. Paketin `Widget/HesapSpendingWidget.swift` dosyasını bu widget klasörüne ekle. **Target Membership yalnızca HesapWidget** olsun.
8. Paketin `Widget/HesapWidgetData.swift` dosyasını da widget klasörüne ekle. Sağdaki File Inspector'da **Target Membership yalnızca HesapWidget** olsun. Ana uygulamanın veri yazma kodu ContentView.swift içinde hazırdır; bu ek dosyayı ana uygulamaya dahil etme.
9. `Widget/en.lproj` ve `Widget/tr.lproj` klasörlerini widget klasörüne ekle; yalnızca widget hedefinin kaynakları olsun.

`HesapWidget` klasörü, ana `Hesap` klasörünün yanında olmalı. Widget'ın `@main` dosyasını ana uygulamanın Swift dosyaları arasına koymak iki giriş noktası oluşturur.

Widget hedefinin Minimum Deployment değeri ana uygulamanınkiyle aynı olabilir. Build Settings altında Swift Language Version değerini uygulamadaki gibi Swift 5 tut. Widget hedefinde Default Actor Isolation ayarı görünüyorsa Nonisolated seç.

## 3. App Groups'u iki hedefte de aç

1. Xcode'da mavi proje simgesine tıkla. TARGETS altında **Hesap** seç.
2. **Signing & Capabilities → + Capability → App Groups** ekle.
3. App Groups altındaki **+** ile şu grubu oluştur ve işaretle:

   `group.com.ates.hesap`

4. TARGETS altında **HesapWidget** seçip aynı App Groups yeteneğini ekle ve **aynı grubu** işaretle.
5. İki hedefte de aynı Team ve Automatically manage signing seçili olsun. Xcode grubun kaydını ve provisioning profile güncellemesini kendi hesabınla yapar.

`HesapWidget.entitlements` beklenen grup kaydının örneğidir. Xcode'un oluşturduğu mevcut entitlement dosyalarında başka ayarlar varsa onları koruyarak bu grubu ekle. Grup adını değiştirmen gerekiyorsa `HesapWidgetData.swift` içindeki `appGroupIdentifier` ile iki hedefteki grup da aynı olmalı.

Paylaşılan veri yalnızca günlük hedef, dil ve güncelleme tarihidir. Finans kayıtları ve işlem geçmişi widget'a kopyalanmaz; sunucuya veri gönderilmez.

## 4. Gizlilik manifestini ekle

Paketin `Widget/PrivacyInfo.xcprivacy` dosyasını iki hedefin de kaynaklarına dahil et. Bu manifest, aynı App Group içinde UserDefaults kullanımını `1C8F.1` gerekçesiyle bildirir.

Projede zaten PrivacyInfo.xcprivacy varsa bu dosyanın `NSPrivacyAccessedAPITypes` kaydını mevcut manifeste birleştir; aynı hedefe iki PrivacyInfo.xcprivacy kopyası ekleme. Mevcut diğer gizlilik kayıtlarını koru.

## 5. Çalıştır ve widget'ı ekle

1. Xcode'da **Hesap** şemasını ve iPhone'unu seçip çalıştır.
2. Uygulamada günlük harcama hedefini kaydet. Örneğin hedef 1.000 TL ise ayın 29'unda widget 29.000 TL gösterir.
3. iPhone ana ekranında boş yere basılı tut → Düzenle / Widget Ekle → **Hesap** → orta boy widget → Widget Ekle.
4. Widget'ın tamamına dokununca Hesap açılır.
5. Uygulamada hedefi veya dili değiştir; widget için yenileme istenir. iOS yenileme zamanını yönetir. Gün değişimleri ve ay başında tutarın sıfırdan yeni aya göre hesaplanması için 35 günlük zaman çizelgesi hazırlanır.

Hesap widget listesinde yoksa Xcode'da ana uygulamanın Build Phases bölümünde widget `.appex` dosyasının **Embed Foundation Extensions** altında bulunduğunu ve iki hedefin signing ayarlarını kontrol et. Widget “Hesap’ı açıp harcama hedefini kaydet.” diyorsa iki hedefin aynı App Group'u kullandığını kontrol edip uygulamayı bir kez aç ve hedefi kaydet.

## Kontrol sınırı

Bu bulut ortamında Xcode ve iOS SDK yok. HTML davranışları, veri köprüsü ve örnek yerleşimler tarayıcıda kontrol edilebilir; WidgetKit derlemesi ve gerçek ana ekran görünümü Xcode/iPhone üzerinde doğrulanmalıdır. Xcode'da Widget Preview, birden fazla iPhone boyutunda kontrol için kullanılabilir.
