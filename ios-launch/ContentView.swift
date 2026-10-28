import SwiftUI
import UIKit
import WebKit
import UniformTypeIdentifiers
import UserNotifications

// iOS 15 ve üzeri. HTML dosyası: finans-ilk-prototip.html
struct ContentView: View {
    var body: some View {
        HesapWebView()
            .ignoresSafeArea()
    }
}

struct HesapWebView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> HesapViewController { HesapViewController() }
    func updateUIViewController(_ controller: HesapViewController, context: Context) {}
}

final class HesapViewController: UIViewController, WKScriptMessageHandler,
    WKNavigationDelegate, UIDocumentPickerDelegate, UNUserNotificationCenterDelegate, UIScrollViewDelegate {
    private var webView: WKWebView!
    private let loadingCover = UIView()
    private let loadErrorLabel = UILabel()
    private let retryButton = UIButton(type: .system)
    private var contentRevealed = false
    private var exporting = false
    private var exportedURL: URL?
    private var scheduleRevision = 0
    private let notificationPrefix = "hesap."

    override func viewDidLoad() {
        super.viewDidLoad()
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.ignoresViewportScaleLimits = false
        configuration.userContentController.add(self, name: "hesap")
        // Wait for the HTML's initial layout and paint; do not wait for exchange-rate requests.
        let readyScript = WKUserScript(
            source: """
            requestAnimationFrame(() => requestAnimationFrame(() => {
                window.webkit.messageHandlers.hesap.postMessage({action: 'ready'});
            }));
            """,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: true
        )
        configuration.userContentController.addUserScript(readyScript)
        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = self
        webView.scrollView.bounces = false
        webView.scrollView.bouncesZoom = false
        webView.scrollView.minimumZoomScale = 1
        webView.scrollView.maximumZoomScale = 1
        webView.scrollView.pinchGestureRecognizer?.isEnabled = false
        webView.scrollView.delegate = self
        webView.isOpaque = false
        let background = UIColor(named: "HesapLaunchBackground")
            ?? UIColor(red: 48.0/255.0, green: 70.0/255.0, blue: 96.0/255.0, alpha: 1)
        view.backgroundColor = background
        webView.scrollView.backgroundColor = background
        webView.backgroundColor = background
        webView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(webView)
        NSLayoutConstraint.activate([
            webView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            webView.topAnchor.constraint(equalTo: view.topAnchor),
            webView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        configureLoadingCover(background: background)
        UNUserNotificationCenter.current().delegate = self
        loadPrototype()
        NotificationCenter.default.addObserver(self, selector: #selector(refresh),
            name: UIApplication.didBecomeActiveNotification, object: nil)
        NotificationCenter.default.addObserver(self, selector: #selector(refresh),
            name: UIApplication.significantTimeChangeNotification, object: nil)
    }

    private func configureLoadingCover(background: UIColor) {
        loadingCover.backgroundColor = background
        loadingCover.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(loadingCover)
        NSLayoutConstraint.activate([
            loadingCover.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            loadingCover.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            loadingCover.topAnchor.constraint(equalTo: view.topAnchor),
            loadingCover.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        let image = UIImage(named: "HesapLaunchLogo")
            ?? Bundle.main.url(forResource: "AppIcon-1024", withExtension: "png")
                .flatMap { UIImage(contentsOfFile: $0.path) }
        let logo = UIImageView(image: image)
        logo.contentMode = .scaleAspectFit
        logo.isAccessibilityElement = true
        logo.accessibilityLabel = "Hesap yükleniyor"
        logo.translatesAutoresizingMaskIntoConstraints = false
        loadingCover.addSubview(logo)

        loadErrorLabel.textColor = .white
        loadErrorLabel.font = .preferredFont(forTextStyle: .body)
        loadErrorLabel.numberOfLines = 0
        loadErrorLabel.textAlignment = .center
        loadErrorLabel.isHidden = true
        loadErrorLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingCover.addSubview(loadErrorLabel)

        retryButton.setTitle("Tekrar dene", for: .normal)
        retryButton.setTitleColor(.white, for: .normal)
        retryButton.titleLabel?.font = .preferredFont(forTextStyle: .headline)
        retryButton.isHidden = true
        retryButton.translatesAutoresizingMaskIntoConstraints = false
        retryButton.addTarget(self, action: #selector(loadPrototype), for: .touchUpInside)
        loadingCover.addSubview(retryButton)

        NSLayoutConstraint.activate([
            logo.centerXAnchor.constraint(equalTo: loadingCover.centerXAnchor),
            logo.centerYAnchor.constraint(equalTo: loadingCover.centerYAnchor),
            logo.widthAnchor.constraint(equalToConstant: 192),
            logo.heightAnchor.constraint(equalToConstant: 192),
            loadErrorLabel.topAnchor.constraint(equalTo: logo.bottomAnchor, constant: 24),
            loadErrorLabel.leadingAnchor.constraint(equalTo: loadingCover.leadingAnchor, constant: 24),
            loadErrorLabel.trailingAnchor.constraint(equalTo: loadingCover.trailingAnchor, constant: -24),
            retryButton.topAnchor.constraint(equalTo: loadErrorLabel.bottomAnchor, constant: 12),
            retryButton.centerXAnchor.constraint(equalTo: loadingCover.centerXAnchor),
            retryButton.heightAnchor.constraint(greaterThanOrEqualToConstant: 44)
        ])
    }

    @objc private func loadPrototype() {
        contentRevealed = false
        loadingCover.layer.removeAllAnimations()
        loadingCover.alpha = 1
        loadingCover.isHidden = false
        loadErrorLabel.isHidden = true
        retryButton.isHidden = true
        guard let file = Bundle.main.url(forResource: "finans-ilk-prototip", withExtension: "html") else {
            showLoadError("Uygulama dosyası bulunamadı.")
            return
        }
        webView.loadFileURL(file, allowingReadAccessTo: file.deletingLastPathComponent())
    }

    private func revealContent() {
        guard !contentRevealed else { return }
        contentRevealed = true
        if UIAccessibility.isReduceMotionEnabled {
            loadingCover.isHidden = true
            return
        }
        UIView.animate(withDuration: 0.18, animations: {
            self.loadingCover.alpha = 0
        }, completion: { _ in
            if self.contentRevealed { self.loadingCover.isHidden = true }
        })
    }

    private func showLoadError(_ message: String) {
        contentRevealed = false
        loadingCover.layer.removeAllAnimations()
        loadingCover.alpha = 1
        loadingCover.isHidden = false
        loadErrorLabel.text = message
        loadErrorLabel.isHidden = false
        retryButton.isHidden = false
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        guard (error as NSError).code != NSURLErrorCancelled else { return }
        showLoadError("Uygulama yüklenemedi. Tekrar deneyebilirsin.")
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        guard (error as NSError).code != NSURLErrorCancelled else { return }
        showLoadError("Uygulama yüklenemedi. Tekrar deneyebilirsin.")
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        showLoadError("Uygulama içeriği kapandı. Tekrar deneyebilirsin.")
    }

    // Call on the main thread. Payload is serialized rather than interpolated as JS source.
    func viewForZooming(in scrollView: UIScrollView) -> UIView? {
        return nil
    }

    private func deliver(_ payload: [String: Any]) {
        webView.callAsyncJavaScript(
            "window.dispatchEvent(new CustomEvent('hesap-native', { detail: payload }));",
            arguments: ["payload": payload], in: nil, in: .page, completionHandler: nil)
    }
    @objc private func refresh() {
        webView.evaluateJavaScript("window.Hesap?.refreshNotifications()", completionHandler: nil)
    }

    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        // Only accept commands from the bundled top-level page.
        guard message.frameInfo.isMainFrame,
              message.frameInfo.request.url?.isFileURL == true,
              webView.url?.lastPathComponent == "finans-ilk-prototip.html",
              let body = message.body as? [String: Any], let action = body["action"] as? String else { return }
        switch action {
        case "ready":
            revealContent()
        case "requestPermission":
            UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                DispatchQueue.main.async { self.deliver(["type": "permission", "granted": granted]); self.refresh() }
            }
        case "schedule":
            replaceSchedule(body["notifications"] as? [[String: Any]] ?? [], enabled: body["enabled"] as? Bool ?? true)
        case "export":
            guard presentedViewController == nil, let content = body["content"] as? String,
                  content.utf8.count <= 20 * 1024 * 1024 else { return }
            do {
                let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
                try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
                let filename = "Hesap-yedek-\(ISO8601DateFormatter().string(from: Date()).prefix(10)).json"
                let file = directory.appendingPathComponent(filename)
                try Data(content.utf8).write(to: file, options: .atomic)
                exportedURL = file
                exporting = true
                let picker = UIDocumentPickerViewController(forExporting: [file], asCopy: true)
                picker.delegate = self
                present(picker, animated: true)
            } catch { deliver(["type": "error", "message": "Yedek dosyası oluşturulamadı."]) }
        case "import":
            guard presentedViewController == nil else { return }
            exporting = false
            let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.json], asCopy: true)
            picker.allowsMultipleSelection = false
            picker.delegate = self
            present(picker, animated: true)
        default: break
        }
    }

    private func replaceSchedule(_ entries: [[String: Any]], enabled: Bool) {
        scheduleRevision += 1
        let revision = scheduleRevision
        let center = UNUserNotificationCenter.current()
        center.getPendingNotificationRequests { requests in
            DispatchQueue.main.async {
                guard revision == self.scheduleRevision else { return }
                center.removePendingNotificationRequests(withIdentifiers: requests.map(\.identifier).filter { $0.hasPrefix(self.notificationPrefix) })
                guard enabled else { return }
                // The HTML sends the next 60 reminders, leaving headroom under iOS's 64-request limit.
                for entry in entries.prefix(60) {
                    guard let id = entry["id"] as? String, let date = entry["date"] as? String,
                          let hour = entry["hour"] as? Int, let minute = entry["minute"] as? Int,
                          let text = entry["body"] as? String else { continue }
                    let parts = date.split(separator: "-").compactMap { Int($0) }
                    guard parts.count == 3 else { continue }
                    var components = DateComponents()
                    components.year = parts[0]; components.month = parts[1]; components.day = parts[2]
                    components.hour = hour; components.minute = minute
                    // No fixed time zone: these are local wall-clock reminders.
                    let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
                    let content = UNMutableNotificationContent()
                    content.title = "Hesap"
                    content.body = text
                    content.sound = .default
                    center.add(UNNotificationRequest(identifier: self.notificationPrefix + id, content: content, trigger: trigger)) { error in
                        if error != nil { DispatchQueue.main.async { self.deliver(["type": "error", "message": "Bir hatırlatma zamanlanamadı."]) } }
                    }
                }
            }
        }
    }

    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        if exporting { deliver(["type": "exported"]); cleanupExport(); return }
        guard let file = urls.first else { return }
        let scoped = file.startAccessingSecurityScopedResource()
        defer { if scoped { file.stopAccessingSecurityScopedResource() } }
        do {
            let size = try file.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? Int.max
            guard size <= 20 * 1024 * 1024 else { throw CocoaError(.fileReadTooLarge) }
            let data = try Data(contentsOf: file)
            guard let payload = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw CocoaError(.fileReadCorruptFile) }
            deliver(["type": "import", "payload": payload])
        } catch { deliver(["type": "error", "message": "Dosya okunamadı; geçerli bir Hesap yedeği seç."]) }
    }
    func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) { cleanupExport() }
    private func cleanupExport() {
        if let file = exportedURL { try? FileManager.default.removeItem(at: file.deletingLastPathComponent()) }
        exportedURL = nil; exporting = false
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else { decisionHandler(.cancel); return }
        if url.isFileURL && url.lastPathComponent == "finans-ilk-prototip.html" { decisionHandler(.allow); return }
        if url.scheme == "mailto" { UIApplication.shared.open(url) }
        decisionHandler(.cancel)
    }
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        DispatchQueue.main.async { self.refresh() }; completionHandler([.banner, .sound])
    }
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        DispatchQueue.main.async { self.refresh(); self.webView.evaluateJavaScript("document.getElementById('notifications-open')?.click()", completionHandler: nil) }
        completionHandler()
    }
}
