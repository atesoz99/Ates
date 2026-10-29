import Foundation

// Widget target only. ContentView.swift writes this schema to the same App Group key.
struct HesapWidgetSnapshot: Codable {
    let dailyGoal: Double
    let language: String
    let updatedAt: Date

    var locale: Locale { Locale(identifier: language == "en" ? "en_GB" : "tr_TR") }
    var english: Bool { language == "en" }

    func target(on date: Date) -> Double {
        max(0, dailyGoal) * Double(HesapWidgetStore.calendar.component(.day, from: date))
    }

    func amount(on date: Date) -> String {
        let formatter = NumberFormatter()
        formatter.locale = locale
        formatter.numberStyle = .currency
        formatter.currencyCode = "TRY"
        formatter.currencySymbol = "₺"
        formatter.minimumFractionDigits = 0
        formatter.maximumFractionDigits = 0
        formatter.usesGroupingSeparator = true
        return formatter.string(from: NSNumber(value: target(on: date))) ?? "₺0"
    }

    func dayLabel(on date: Date) -> String {
        let day = HesapWidgetStore.calendar.component(.day, from: date)
        return english ? "Day \(day) of the month" : "Ayın \(day). günü"
    }
}

enum HesapWidgetStore {
    static let appGroupIdentifier = "group.com.ates.hesap"
    static let kind = "HesapSpendingWidget"
    private static let snapshotKey = "hesap.spendingWidget.v1"

    static var calendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = .autoupdatingCurrent
        return calendar
    }

    private static var sharedDefaults: UserDefaults? {
        // The main app keeps working when the optional widget capability is not configured yet.
        guard FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier) != nil else { return nil }
        return UserDefaults(suiteName: appGroupIdentifier)
    }

    static func load() -> HesapWidgetSnapshot? {
        guard let bytes = sharedDefaults?.data(forKey: snapshotKey),
              let snapshot = try? JSONDecoder().decode(HesapWidgetSnapshot.self, from: bytes),
              snapshot.dailyGoal.isFinite, snapshot.dailyGoal >= 0,
              snapshot.dailyGoal <= 1e15, ["tr", "en"].contains(snapshot.language) else { return nil }
        return snapshot
    }

    static func timelineDates(from now: Date) -> [Date] {
        let calendar = calendar
        let start = calendar.startOfDay(for: now)
        return [now] + (1...35).compactMap { calendar.date(byAdding: .day, value: $0, to: start) }
    }
}
