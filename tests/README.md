# Localisation checks

Requires Python 3, Playwright for Python and Chromium. The scripts use an installed `chromium`/`google-chrome` executable when available, otherwise Playwright's Chromium. HTTP requests are intercepted locally; no live financial services or customer data are used. The browser clock is fixed to keep date-dependent cases repeatable.

```sh
python -m pip install playwright
python -m playwright install chromium
python tests/test_localisation.py
python tests/test_localisation_errors.py
python tests/test_tracking_updates.py
python tests/test_trade_refinements.py
python tests/test_portfolio_layout.py
python tests/test_eurobond_widget.py
python tests/test_iphone_layouts.py
python tests/test_trade_net.py
```

Coverage includes Turkish/English switching, numeric input conversion, preservation of canonical asset identifiers and custom names, backed-up language preferences, old notification opt-out migration, notifications and bridge messages, empty states, error messages, and iPhone-width overflow checks. These browser checks do not compile Swift, inspect Apple’s calendar on a real iPhone, or test delivery of iOS system notifications.

Trade checks cover the native calendar language bridge, future-date rejection, deposit maturity dates, year/month filtering and transaction-date ordering, grouped fractional quantities, sale form spacing, backup arrow presentation and preservation of existing preferences. With the native calendar capability enabled, date fields retain canonical ISO values in hidden controls; tests that bypass the calendar set those controls and dispatch change events.

The widget snapshot bridge is tested for target/language-only payloads and deduplication. Eurobond checks cover both currencies, insufficient/exact/fractional coverage and hidden holdings in allocation charts. iPhone checks cover 10 portrait viewports and simulated safe areas across two languages, two themes and six screens (240 cases). The HTML widget preview checks medium layout fit; it does not render native WidgetKit. Net summary checks cover year/month filtering, negative/zero totals and equal line spacing.
