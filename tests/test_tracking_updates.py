"""Regression checks for year-scoped comparisons, monthly entries and exchange-rate display."""
from pathlib import Path
from datetime import datetime, timezone
import shutil
from playwright.sync_api import sync_playwright
source=(Path(__file__).resolve().parents[1]/'finans-ilk-prototip.html').read_text()
fixture={'capital':[{'id':'old','date':'2025-09-01','amount':1000000,'fxRate':40}, {'id':'a','date':'2026-09-01','amount':1000000,'fxRate':40}, {'id':'b','date':'2026-10-01','amount':1200000,'fxRate':40}], 'budgets':[{'id':'i','month':'2026-09','income':100000,'expense':50000},{'id':'j','month':'2026-10','income':100000,'expense':60000}], 'theme':'dark'}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844})
 page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def net(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40.12345}})
  else:r.abort()
 page.route('https://**/*',net);page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'))
 page.goto('http://localhost/');page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',fixture);page.reload();page.wait_for_timeout(300)
 page.locator('[data-tab=track]').click();page.select_option('#tracking-year','2025');page.wait_for_timeout(150)
 assert page.locator('#previous-month-comparison').is_hidden()
 assert page.locator('#capital-year').input_value()=='2025'
 assert page.locator('#capital-month').input_value()=='9'
 assert page.locator('#capital-amount').input_value()=='1.000.000'
 assert page.locator('#capital-change').evaluate('e=>getComputedStyle(e).fontSize')==page.locator('#capital-rate-status').evaluate('e=>getComputedStyle(e).fontSize')
 assert page.locator('#capital-change').inner_text()=='Karşılaştırılabilecek veri yok.'
 assert page.locator('#capital-change-percent').is_hidden()
 page.select_option('#tracking-year','2026');page.wait_for_timeout(150)
 assert page.locator('#previous-month-comparison').is_visible()
 assert page.locator('#capital-change-percent').is_visible()
 assert page.locator('#capital-month').input_value()=='10'
 for theme in ['dark','light']:
  page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
  for id in ['capital-change-percent','capital-change-usd']:
   label=page.locator('#'+id+' .comparison-label')
   assert label.inner_text().endswith(':')
   assert label.evaluate('e=>getComputedStyle(e).fontSize')==page.locator('#latest-capital-usd').evaluate('e=>getComputedStyle(e).fontSize')
   assert label.evaluate('e=>getComputedStyle(e).color')==page.locator('#latest-capital-usd').evaluate('e=>getComputedStyle(e).color')
   assert label.evaluate('e=>getComputedStyle(e).color')!=page.locator('#'+id).evaluate('e=>getComputedStyle(e).color')

 page.select_option('#capital-year','2025');page.select_option('#capital-month','9')
 assert page.locator('#capital-amount').input_value()=='1.000.000'
 page.locator('#capital-form .primary').click();page.wait_for_timeout(250)
 assert page.locator('#capital-amount').input_value()=='1.000.000'
 assert page.locator('#capital-year').input_value()=='2025'
 assert page.locator('#capital-month').input_value()=='9'
 for link in ['#capital-period','#home .section-head [data-go=track]']:
  page.select_option('#tracking-year','2025');page.select_option('#capital-year','2025');page.select_option('#capital-month','9')
  page.locator('[data-tab=home]').click();page.wait_for_timeout(300);page.locator(link).click();page.wait_for_timeout(350)
  assert page.locator('#tracking-year').input_value()=='2026'
  assert page.locator('#capital-year').input_value()=='2026'
  assert page.locator('#capital-month').input_value()=='10'
  assert page.locator('#capital-amount').input_value()=='1.200.000'
 page.locator('[data-tab=term]').click();page.locator('#term-start').fill('2026-10-29');page.wait_for_timeout(300)
 assert page.locator('#start-fx').input_value()=='40,12'
 assert '40,12' in page.locator('#rate-status').inner_text()
 page.locator('[data-tab=trade]').click();page.wait_for_timeout(300)
 page.select_option('#asset','Dolar');page.locator('#trade-date').fill('2026-10-29');page.wait_for_timeout(300)
 assert page.locator('#unit-price').input_value()=='40,12',page.locator('#unit-price').input_value()
 page.locator('#account-open').click();page.select_option('#language-select','en');page.locator('#account-close').click()
 page.locator('[data-tab=track]').click();page.select_option('#tracking-year','2025');page.wait_for_timeout(200)
 assert page.locator('#capital-change').inner_text()=='No data available for comparison.'
 assert page.locator('#previous-month-comparison').is_hidden()
 assert not errors,errors
 b.close()
 print('PASS: year-scoped comparisons, insufficient-data message in both languages, grouped entries after save, both home links reset year/month, two-decimal USD rate inputs.')
