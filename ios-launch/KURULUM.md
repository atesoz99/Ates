# Hesap — logolu iPhone açılışı

Bu paket iki aşamayı aynı görünümle karşılar: iOS'un ilk açılış ekranı ve HTML'nin WKWebView içinde yüklenmesi. Son onaylanan mavi ikon ortada 192×192 punto gösterilir. Beyaz açılış yerine koyu mavi arka plan kullanılır. HTML'nin ilk çizimi hazır olduğunda kapak kapanır; internetten kurların gelmesi beklenmez. Dosya bulunamazsa veya yüklenemezse logo altında tekrar deneme seçeneği görünür.

## Xcode'a ekleme

1. Var olan **ContentView.swift** içeriğinin tamamını bu paketteki dosyayla değiştir. Aynı tanımları içeren ikinci bir `HesapWebView.swift` ekleme; varsa uygulama hedefinden çıkar. `MyApp.swift` dosyasını değiştirme.
2. Paketteki **LaunchAssets.xcassets** ve **LaunchScreen.storyboard** dosyalarını/klasörünü Xcode'daki uygulama grubuna sürükle. Dosyalar projenin dışında kalıyorsa **Copy items if needed** seç. Uygulama hedefinin **Target Membership** işaretli olsun. Mevcut Assets.xcassets içeriğini silme. Ayrı katalogdaki iki kaynak HesapLaunchLogo ve HesapLaunchBackground adlarını kullanır.
3. Uygulama hedefinde **Build Settings → Launch Screen Generation** ayarı varsa **No** yap. **Info → Custom iOS Target Properties** altında **Launch screen interface file base name** (`UILaunchStoryboardName`) anahtarını **String** türünde **LaunchScreen** olarak ekle/ayarla. Uzantı yazma. General sekmesinde Launch Screen File alanı görünüyorsa orada da **LaunchScreen** seçili olmalı. Mevcut bir LaunchScreen.storyboard varsa ikinci kopya eklemek yerine onun içeriğini değiştir.
4. Son HTML dosyan **finans-ilk-prototip.html** adıyla uygulama hedefinde kalmalı. HTML'yi bu değişiklik için yeniden düzenlemene gerek yok. Logo runtime'da AppIcon kaynağına bağlı değildir; paketteki HesapLaunchLogo kullanılır.
5. **⌘B** ile derle, gerçek iPhone'da çalıştır. İlk açılış ekranını görmek için uygulamayı uygulama değiştiriciden kapatıp yeniden aç. iOS eski launch screen görüntüsünü önbellekte tutabilir; önce **Product → Clean Build Folder** ile yeniden derle ve cihazı yeniden başlat. Kayıtlarını yedeklemeden uygulamayı silme.

## Kontrol

Soğuk açılışta mavi arka plan ve ortalanmış logo görünmeli; HTML çizildiğinde ana sayfaya geçmeli. İnternet kapalıyken de ana sayfa açılmalı. Açık/koyu tema, yatay/dikey yön ve eski kayıtlara erişim kontrol edilmeli. Bildirim ve dosya yedekleme köprüsü ile büyütme engeli korundu.

Bu çalışma ortamında Xcode/iOS SDK bulunmuyor. Storyboard XML'i, varlık dosyaları, logo boyutu ve açılış mesajının HTML'den gönderilmesi kontrol edildi. Swift derlemesi, storyboard'un ibtool ile derlenmesi ve gerçek iPhone açılışı burada doğrulanamadı. Bu paket Xcode projesine henüz uygulanmış değildir.
