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
    private var interfaceLanguage = Locale.preferredLanguages.first?.hasPrefix("en") == true ? "en" : "tr"
    private weak var launchLogo: UIImageView?
    private var loadErrorText = ""
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
        configuration.userContentController.addUserScript(WKUserScript(
            source: "window.HesapNativeDatePicker = true;",
            injectionTime: .atDocumentStart, forMainFrameOnly: true))
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
        launchLogo = logo
        logo.contentMode = .scaleAspectFit
        logo.isAccessibilityElement = true
        logo.accessibilityLabel = nativeText("Hesap yükleniyor")
        logo.translatesAutoresizingMaskIntoConstraints = false
        loadingCover.addSubview(logo)

        loadErrorLabel.textColor = .white
        loadErrorLabel.font = UIFont(name: "Arial", size: 17)
        loadErrorLabel.numberOfLines = 0
        loadErrorLabel.textAlignment = .center
        loadErrorLabel.isHidden = true
        loadErrorLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingCover.addSubview(loadErrorLabel)

        retryButton.setTitle(nativeText("Tekrar dene"), for: .normal)
        retryButton.setTitleColor(.white, for: .normal)
        retryButton.titleLabel?.font = UIFont(name: "Arial-BoldMT", size: 17)
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
        loadErrorText = message
        loadErrorLabel.text = nativeText(message)
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

    private func nativeText(_ text: String) -> String {
        guard interfaceLanguage == "en" else { return text }
        let english = [
            "Hesap yükleniyor": "Hesap is loading",
            "Tekrar dene": "Try again",
            "Uygulama dosyası bulunamadı.": "The app file could not be found.",
            "Uygulama yüklenemedi. Tekrar deneyebilirsin.": "The app could not be loaded. Please try again.",
            "Uygulama içeriği kapandı. Tekrar deneyebilirsin.": "The app content was closed. Please try again.",
            "Yedek dosyası oluşturulamadı.": "The backup file could not be created.",
            "Bir hatırlatma zamanlanamadı.": "A reminder could not be scheduled.",
            "Dosya okunamadı; geçerli bir Hesap yedeği seç.": "The file could not be read. Please select a valid Hesap backup."
        ]
        return english[text] ?? text
    }

    private func deliver(_ payload: [String: Any]) {
        var translatedPayload = payload
        if let message = payload["message"] as? String { translatedPayload["message"] = nativeText(message) }
        webView.callAsyncJavaScript(
            "window.dispatchEvent(new CustomEvent('hesap-native', { detail: payload }));",
            arguments: ["payload": translatedPayload], in: nil, in: .page, completionHandler: nil)
    }
    private func presentDatePicker(_ body: [String: Any]) {
        guard presentedViewController == nil,
              let field = body["field"] as? String,
              ["trade-date", "term-start", "term-end"].contains(field) else { return }
        let english = (body["language"] as? String ?? interfaceLanguage) == "en"
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = .current
        let today = calendar.startOfDay(for: Date())
        let minimum = field == "term-end"
            ? calendar.date(byAdding: .day, value: 1, to: today) ?? today
            : calendar.date(from: DateComponents(year: 1900, month: 1, day: 1)) ?? .distantPast
        let maximum = field == "term-end"
            ? calendar.date(from: DateComponents(year: 2100, month: 12, day: 31)) ?? .distantFuture
            : today
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = calendar
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.isLenient = false
        let initial = (body["value"] as? String).flatMap { formatter.date(from: $0) } ?? (field == "term-end" ? minimum : today)
        let picker = HesapDatePickerController(
            english: english, date: min(max(initial, minimum), maximum),
            minimum: minimum, maximum: maximum
        ) { [weak self] selected in
            guard selected >= minimum, selected <= maximum else { return }
            self?.deliver(["type": "dateSelected", "field": field, "value": formatter.string(from: selected)])
        }
        let navigation = UINavigationController(rootViewController: picker)
        navigation.overrideUserInterfaceStyle = body["dark"] as? Bool == true ? .dark : .light
        let calendarBackground = UIColor { traits in
            traits.userInterfaceStyle == .dark ? UIColor(white: 0.08, alpha: 1) : .systemBackground
        }
        navigation.view.backgroundColor = calendarBackground
        let barAppearance = UINavigationBarAppearance()
        barAppearance.configureWithOpaqueBackground()
        barAppearance.backgroundColor = calendarBackground
        navigation.navigationBar.standardAppearance = barAppearance
        navigation.navigationBar.scrollEdgeAppearance = barAppearance
        // Give the entire system calendar enough room instead of clipping it inside a popover.
        navigation.modalPresentationStyle = .pageSheet
        if let sheet = navigation.sheetPresentationController {
            if #available(iOS 16.0, *) {
                let calendarHeight = UISheetPresentationController.Detent.custom(
                    identifier: .init("hesapCalendar")
                ) { context in
                    min(500, context.maximumDetentValue)
                }
                sheet.detents = [calendarHeight, .large()]
                sheet.selectedDetentIdentifier = calendarHeight.identifier
            } else {
                sheet.detents = [.large()]
            }
            sheet.prefersGrabberVisible = true
        }
        present(navigation, animated: true)
    }

    @objc private func refresh() {
        webView.evaluateJavaScript("window.Hesap?.refreshNotifications(undefined, true)", completionHandler: nil)
    }

    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        // Only accept commands from the bundled top-level page.
        guard message.frameInfo.isMainFrame,
              message.frameInfo.request.url?.isFileURL == true,
              webView.url?.lastPathComponent == "finans-ilk-prototip.html",
              let body = message.body as? [String: Any], let action = body["action"] as? String else { return }
        switch action {
        case "language":
            guard let selected = body["language"] as? String, ["tr", "en"].contains(selected) else { return }
            interfaceLanguage = selected
            retryButton.setTitle(nativeText("Tekrar dene"), for: .normal)
            launchLogo?.accessibilityLabel = nativeText("Hesap yükleniyor")
            if !loadErrorText.isEmpty { loadErrorLabel.text = nativeText(loadErrorText) }
        case "pickDate":
            presentDatePicker(body)
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
                let prefix = interfaceLanguage == "en" ? "Hesap-backup" : "Hesap-yedek"
                let filename = "\(prefix)-\(ISO8601DateFormatter().string(from: Date()).prefix(10)).json"
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
        center.getNotificationSettings { settings in
            center.getPendingNotificationRequests { requests in
                DispatchQueue.main.async {
                    guard revision == self.scheduleRevision else { return }
                    let oldIDs = requests.map(\.identifier).filter {
                        $0.hasPrefix(self.notificationPrefix)
                    }
                    center.removePendingNotificationRequests(withIdentifiers: oldIDs)
                    // OS permission controls system alerts only; the in-app inbox is always available.
                    let permitted = settings.authorizationStatus == .authorized
                        || settings.authorizationStatus == .provisional
                        || settings.authorizationStatus == .ephemeral
                    guard enabled && permitted else { return }
                    for entry in entries.prefix(60) {
                        guard let id = entry["id"] as? String,
                              let date = entry["date"] as? String,
                              let hour = entry["hour"] as? Int,
                              let minute = entry["minute"] as? Int,
                              let text = entry["body"] as? String else { continue }
                        let parts = date.split(separator: "-").compactMap { Int($0) }
                        guard parts.count == 3 else { continue }
                        var components = DateComponents()
                        components.year = parts[0]
                        components.month = parts[1]
                        components.day = parts[2]
                        components.hour = hour
                        components.minute = minute
                        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
                        let content = UNMutableNotificationContent()
                        content.title = "Hesap"
                        content.body = text
                        content.sound = .default
                        let request = UNNotificationRequest(
                            identifier: self.notificationPrefix + id,
                            content: content,
                            trigger: trigger
                        )
                        center.add(request) { error in
                            if error != nil {
                                DispatchQueue.main.async {
                                    self.deliver(["type": "error", "message": "Bir hatırlatma zamanlanamadı."])
                                }
                            }
                        }
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

// Apple's calendar control, with the app's locale and no clear/reset action.
final class HesapDatePickerController: UIViewController {
    private let picker = UIDatePicker()
    private let english: Bool
    private let selected: (Date) -> Void

    init(english: Bool, date: Date, minimum: Date, maximum: Date, selected: @escaping (Date) -> Void) {
        self.english = english
        self.selected = selected
        super.init(nibName: nil, bundle: nil)
        picker.datePickerMode = .date
        picker.preferredDatePickerStyle = .inline
        picker.locale = Locale(identifier: english ? "en_GB" : "tr_TR")
        var calendar = Calendar(identifier: .gregorian)
        calendar.locale = picker.locale
        calendar.firstWeekday = 2
        calendar.timeZone = .current
        picker.calendar = calendar
        picker.timeZone = .current
        picker.minimumDate = minimum
        picker.maximumDate = maximum
        picker.setDate(date, animated: false)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor { traits in
            traits.userInterfaceStyle == .dark ? UIColor(white: 0.08, alpha: 1) : .systemBackground
        }
        picker.backgroundColor = .clear
        title = english ? "Date" : "Tarih"
        navigationItem.leftBarButtonItem = UIBarButtonItem(
            title: english ? "Cancel" : "Vazgeç", style: .plain, target: self, action: #selector(cancel))
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            title: english ? "Done" : "Tamam", style: .done, target: self, action: #selector(confirm))
        picker.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(picker)
        NSLayoutConstraint.activate([
            picker.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 12),
            picker.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 12),
            picker.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -12),
            picker.bottomAnchor.constraint(lessThanOrEqualTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -12)
        ])
    }

    @objc private func cancel() { dismiss(animated: true) }
    @objc private func confirm() {
        selected(picker.date)
        dismiss(animated: true)
    }
}
