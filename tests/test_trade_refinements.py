"""Trade period filtering, grouped quantities, date controls and first-install preferences."""
from pathlib import Path
from datetime import datetime, timezone
import shutil
from playwright.sync_api import sync_playwright
source=(Path(__file__).resolve().parents[1]/'finans-ilk-prototip.html').read_text()
fixture={'trades':[{'id':'jan2','asset':'Dolar','action':'Alış','date':'2026-01-02','quantity':1,'price':40,'createdAt':9999},{'id':'sep','asset':'Dolar','action':'Alış','date':'2026-09-10','quantity':3,'price':40,'createdAt':1},{'id':'jan20','asset':'Dolar','action':'Alış','date':'2026-01-20','quantity':2,'price':40,'createdAt':2},{'id':'old','asset':'Dolar','action':'Alış','date':'2025-12-01','quantity':4,'price':40,'createdAt':99999}]}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def network(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40.12345}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-10-01','average':2000}]})
 page.route('https://**/*',network);page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'))
 page.add_init_script('window.HesapNativeDatePicker=true;window.nativeMessages=[];window.webkit={messageHandlers:{hesap:{postMessage:m=>nativeMessages.push(m)}}};')
 page.goto('http://localhost/');page.wait_for_timeout(200)
 page.locator('#account-open').click();assert page.locator('[data-asset-visibility]').count()==8
 assert page.locator('[data-asset-visibility]:checked').count()==8
 assert page.locator('#account-overlay input[type=checkbox]:checked:not([data-asset-visibility])').count()==0
 assert 'Verilerini yedekle.' in page.locator('#backup-export').inner_text()
 assert page.locator('.backup-actions>p').inner_text()=='Geri yükleme, mevcut kayıtların yerini alır.'
 assert page.locator('.backup-actions>p').evaluate('e=>getComputedStyle(e).marginTop')=='6px'
 assert page.locator('#backup-export svg').evaluate('e=>getComputedStyle(e).width')==page.locator('#account-contact').evaluate('e=>getComputedStyle(e).fontSize')
 assert page.locator('#backup-export .backup-direction path').get_attribute('d')=='M4 12 12 4 M4 4h8v8'
 assert page.locator('#backup-import .backup-direction path').get_attribute('d')=='M12 4 4 12 M4 4v8h8'
 page.locator('#account-close').click()
 page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',fixture);page.reload();page.wait_for_timeout(250);page.locator('[data-tab=trade]').click();page.wait_for_timeout(200)
 assert page.locator('#trade-count').inner_text()=='3 İşlem. 2026'
 assert page.locator('#trade-month option').count()==11
 assert page.locator('#trade-list [data-delete]').evaluate_all('es=>es.map(e=>e.dataset.id)')==['sep','jan20','jan2']
 page.select_option('#trade-month','1');page.wait_for_timeout(100)
 assert page.locator('#trade-count').inner_text()=='2 İşlem. Ocak 2026'
 assert 'Alış: 3 $' in page.locator('#trade-year-summary .trade-card').first.inner_text()
 assert page.locator('#trade-list [data-delete]').evaluate_all('es=>es.map(e=>e.dataset.id)')==['jan20','jan2']
 page.select_option('#trade-year','2025');page.wait_for_timeout(100)
 assert page.locator('#trade-month option').count()==13
 page.select_option('#trade-month','all');assert page.locator('#trade-count').inner_text()=='1 İşlem. 2025'
 page.select_option('#trade-year','2026');page.wait_for_timeout(100)
 page.locator('#trade-date-picker').click()
 assert page.locator('#date-dialog').count()==0
 message=page.evaluate('nativeMessages.filter(m=>m.action==="pickDate").at(-1)')
 assert message['field']=='trade-date' and message['language']=='tr'
 assert page.locator('#trade-date').get_attribute('max')=='2026-10-29'
 page.evaluate("window.dispatchEvent(new CustomEvent('hesap-native',{detail:{type:'dateSelected',field:'trade-date',value:'2026-10-30'}}))")
 assert page.locator('#trade-date').input_value()=='2026-10-29'
 page.evaluate("window.dispatchEvent(new CustomEvent('hesap-native',{detail:{type:'dateSelected',field:'trade-date',value:'2026-10-28'}}))")
 page.wait_for_timeout(150)
 assert page.locator('#trade-date').input_value()=='2026-10-28'
 assert '28.10.2026'==page.locator('#trade-date-picker').inner_text()
 page.locator('#quantity').fill('60000,0001');page.locator('#quantity').blur()
 assert page.locator('#quantity').input_value()=='60.000,0001'
 page.locator('#unit-price').fill('40,12');page.locator('#trade-submit').click();page.wait_for_timeout(200)
 trades=page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).trades')
 assert trades[-1]['quantity']==60000.0001 and trades[-1]['date']=='2026-10-28'
 page.select_option('#action','Satış');page.locator('#quantity').fill('1')
 page.locator('#trade-date').evaluate("e=>{e.value='2026-10-30';e.dispatchEvent(new Event('change',{bubbles:true}))}")
 page.locator('#trade-submit').click();page.wait_for_timeout(100)
 assert len(page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).trades'))==len(trades)
 assert 'bugünden ileri' in page.locator('#toast').inner_text()
 assert page.locator('#trade-submit').evaluate('e=>parseFloat(getComputedStyle(e).marginTop)')>=18
 page.select_option('#asset','Gram altın');page.select_option('#action','Alış');page.wait_for_timeout(150)
 assert 'Dolar bazında karşılaştırma için kullanılır.' in page.locator('#gold-ounce-field').inner_text()
 for el in ['#trade-price-note','#gold-ounce-field>.small']:
  assert page.locator(el).evaluate('e=>parseFloat(getComputedStyle(e).lineHeight)/parseFloat(getComputedStyle(e).fontSize)')<=1.31
 page.locator('#account-open').click();page.select_option('#language-select','en');page.locator('#account-close').click();page.wait_for_timeout(200)
 assert 'transactions. 2026' in page.locator('#trade-count').inner_text()
 assert 'Bought:' in page.locator('#trade-summary').inner_text()
 assert 'Holdings:' in page.locator('#trade-summary').inner_text() or 'Held:' in page.locator('#trade-summary').inner_text()
 assert 'Average purchase cost:' in page.locator('#trade-summary').inner_text()
 assert 'Alış:' not in page.locator('#trade-summary').inner_text()
 page.locator('#trade-date-picker').click()
 assert page.evaluate('nativeMessages.filter(m=>m.action==="pickDate").at(-1).language')=='en'
 page.locator('[data-tab=term]').click();page.locator('#term-end-picker').click()
 assert page.evaluate('nativeMessages.filter(m=>m.action==="pickDate").at(-1).field')=='term-end'
 assert page.locator('#term-end').get_attribute('min')=='2026-10-30'
 page.evaluate("window.dispatchEvent(new CustomEvent('hesap-native',{detail:{type:'dateSelected',field:'term-end',value:'2026-11-01'}}))")
 assert page.locator('#term-end').input_value()=='2026-11-01'
 # Existing preferences survive relaunch; defaults only apply to first launch.
 page.locator('#account-open').click();page.locator('[data-asset-visibility="Euro"]').uncheck();page.locator('#dark-theme-toggle').check();page.reload();page.wait_for_timeout(150);page.locator('#account-open').click()
 assert not page.locator('[data-asset-visibility="Euro"]').is_checked()
 assert page.locator('#dark-theme-toggle').is_checked()
 assert not errors,errors
 browser.close();print('PASS: initial preferences, backup arrows, month/year summary and list filtering, date ordering, native date-picker language bridge, future-date rejection, maturity future dates, grouped fractional quantity save, labels, hint spacing, sale spacing and preserved preferences.')
