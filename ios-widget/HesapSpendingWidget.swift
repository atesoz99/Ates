import SwiftUI
import WidgetKit

struct HesapSpendingEntry: TimelineEntry {
    let date: Date
    let snapshot: HesapWidgetSnapshot?
}

struct HesapSpendingProvider: TimelineProvider {
    private var sample: HesapWidgetSnapshot {
        HesapWidgetSnapshot(dailyGoal: 1000, language: HesapWidgetStore.load()?.language ?? (Locale.preferredLanguages.first?.hasPrefix("en") == true ? "en" : "tr"), updatedAt: Date())
    }

    func placeholder(in context: Context) -> HesapSpendingEntry {
        HesapSpendingEntry(date: Date(), snapshot: sample)
    }

    func getSnapshot(in context: Context, completion: @escaping (HesapSpendingEntry) -> Void) {
        completion(HesapSpendingEntry(date: Date(), snapshot: context.isPreview ? sample : HesapWidgetStore.load()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<HesapSpendingEntry>) -> Void) {
        let snapshot = HesapWidgetStore.load()
        let entries = HesapWidgetStore.timelineDates(from: Date()).map {
            HesapSpendingEntry(date: $0, snapshot: snapshot)
        }
        completion(Timeline(entries: entries, policy: .atEnd))
    }
}

struct HesapSpendingView: View {
    let entry: HesapSpendingEntry
    private let background = Color(red: 34 / 255.0, green: 37 / 255.0, blue: 42 / 255.0)
    private let ink = Color(red: 241 / 255.0, green: 234 / 255.0, blue: 221 / 255.0)
    private let muted = Color(red: 180 / 255.0, green: 175 / 255.0, blue: 165 / 255.0)
    private var english: Bool { entry.snapshot?.english ?? (Locale.preferredLanguages.first?.hasPrefix("en") == true) }

    private var content: some View {
        GeometryReader { geometry in
            VStack(alignment: .leading, spacing: 4) {
                Text(english ? "Spending target to date" : "Bugüne Kadarki Harcama Hedefi")
                    .font(.custom("Arial-BoldMT", size: 16))
                    .foregroundColor(ink)
                    .lineLimit(2)
                Text(entry.snapshot?.dayLabel(on: entry.date) ?? fallbackDayLabel)
                    .font(.custom("Arial", size: 13))
                    .foregroundColor(muted)
                    .lineLimit(1)
                Text(entry.snapshot?.amount(on: entry.date) ?? "—")
                    .font(.custom("Arial-BoldMT", size: 24))
                    .foregroundColor(ink)
                    .lineLimit(1)
                    .minimumScaleFactor(0.55)
                    .padding(.vertical, 3)
                Text(caption)
                    .font(.custom("Arial", size: 15))
                    .foregroundColor(muted)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(geometry.size.height < 150 ? 10 : 14)
        }
        .environment(\.colorScheme, .dark)
    }

    private var fallbackDayLabel: String {
        let day = HesapWidgetStore.calendar.component(.day, from: entry.date)
        return english ? "Day \(day) of the month" : "Ayın \(day). günü"
    }

    private var caption: String {
        guard entry.snapshot != nil else {
            return english ? "Open Hesap and save your spending target." : "Hesap’ı açıp harcama hedefini kaydet."
        }
        return english ? "Your cumulative spending limit up to today." : "Ayın bugününe kadar geçmemen gereken toplam."
    }

    var body: some View {
        if #available(iOS 17.0, *) {
            content.containerBackground(for: .widget) { background }
        } else {
            content.background(background)
        }
    }
}

@main
struct HesapSpendingWidget: Widget {
    private var configuration: some WidgetConfiguration {
        StaticConfiguration(kind: HesapWidgetStore.kind, provider: HesapSpendingProvider()) { entry in
            HesapSpendingView(entry: entry)
        }
        .configurationDisplayName("Hesap")
        .description("widget.description")
        .supportedFamilies([.systemMedium])
        // Tapping a widget without a custom URL opens its containing app.
    }

    var body: some WidgetConfiguration {
        if #available(iOS 17.0, *) {
            configuration.contentMarginsDisabled()
        } else {
            configuration
        }
    }
}

#if DEBUG
struct HesapSpendingWidget_Previews: PreviewProvider {
    static var previews: some View {
        let date = HesapWidgetStore.calendar.date(from: DateComponents(year: 2026, month: 10, day: 29, hour: 12)) ?? Date()
        return Group {
            HesapSpendingView(entry: HesapSpendingEntry(date: date, snapshot: HesapWidgetSnapshot(dailyGoal: 1000, language: "tr", updatedAt: date)))
                .previewContext(WidgetPreviewContext(family: .systemMedium))
                .previewDisplayName("Türkçe")
            HesapSpendingView(entry: HesapSpendingEntry(date: date, snapshot: HesapWidgetSnapshot(dailyGoal: 1000, language: "en", updatedAt: date)))
                .previewContext(WidgetPreviewContext(family: .systemMedium))
                .previewDisplayName("English")
        }
    }
}
#endif
