import json,re,shutil
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'finans-ilk-prototip.html').read_text()
# Test-only access to the translation function for complete static-copy coverage.
source=source.replace('window.Hesap=Object.freeze({','window.__translate=translateText;window.Hesap=Object.freeze({',1)
fixture={'capital':[{'id':'c1','date':'2026-01-01','amount':100000,'fxRate':40},{'id':'c2','date':'2026-02-01','amount':120000,'fxRate':40}], 'budgets':[{'id':'b1','month':'2026-01','income':30000,'expense':10000,'daily':500},{'id':'b2','month':'2026-02','income':35000,'expense':15000,'daily':500}], 'trades':[{'id':'t1','asset':'Dolar','action':'Alış','date':'2026-01-01','quantity':100,'price':40},{'id':'t2','asset':'Gram altın','action':'Alış','date':'2026-01-01','quantity':10,'price':2500,'ounceUsd':2000}], 'terms':[{'id':'term','start':'2026-01-01','tryEnd':'2027-01-01','principal':10000,'income':1000,'startFx':40,'currentFx':40}], 'recurring':[{'id':'r','name':'Gelir','day':1,'amount':1234.56}], 'otherTlInvestment':{'amount':1000,'name':'Gider'},'eurobond':{'usd':10,'eur':0},'monthlyRates':{},'notifications':{'enabled':False},'theme':'light'}
with sync_playwright() as p:
 browser_path=shutil.which('chromium') or shutil.which('google-chrome')
 b=p.chromium.launch(**({'executable_path':browser_path} if browser_path else {}),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 page.clock.install(time=datetime(2026,10,28,12,tzinfo=timezone.utc))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def network(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-28','rates':{'TRY':40}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-01-01','average':2000}]})
 page.route('https://**/*',network)
 page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'))
 page.add_init_script('window.nativeMessages=[];window.webkit={messageHandlers:{hesap:{postMessage:m=>nativeMessages.push(m)}}};')
 page.goto('http://localhost/');page.wait_for_timeout(250)
 page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',fixture);page.reload();page.wait_for_timeout(400)
 assert page.locator('#notify-enabled').count()==0
 assert page.locator('.notification-item').count()>0
 page.locator('[data-tab=trade]').click();page.wait_for_timeout(250)
 page.locator('#quantity').fill('12.5');page.locator('#unit-price').fill('1.234,56')
 page.locator('#account-open').click();page.select_option('#language-select','en');page.wait_for_timeout(100)
 assert page.locator('#unit-price').input_value()=='1,234.56'
 assert page.locator('#quantity').input_value()=='12.5'
 assert page.locator('#action').input_value()=='Alış'
 assert page.locator('#action option').all_text_contents()==['Buy','Sell']
 assert page.locator('#asset option').first.get_attribute('value')=='Dolar'
 assert page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).trades[0].asset')=='Dolar'
 assert page.locator('#language-select option').all_text_contents()==['Turkish','English']
 assert page.evaluate('nativeMessages.filter(m=>m.action==="language").at(-1).language')=='en'
 # All original static labels translate, apart from symbols, numbers, brand and unchanged English currency names.
 class StaticCopy(HTMLParser):
  def __init__(self):super().__init__();self.skip=0;self.strings=set()
  def handle_starttag(self,tag,attrs):
   if tag in ['script','style']:self.skip+=1
   if not self.skip:
    self.strings.update(v for k,v in attrs if k in ['placeholder','aria-label','title','data-title'] and v)
  def handle_endtag(self,tag):
   if tag in ['script','style']:self.skip=max(0,self.skip-1)
  def handle_data(self,value):
   if not self.skip and value.strip():self.strings.add(value.strip())
 copy=StaticCopy();copy.feed(source);originals=sorted(copy.strings)
 results=page.evaluate('(items)=>items.map(s=>[s,__translate(s)])',originals)
 allowed={'English','Türkçe','Hesap','Euro','0','5','×','—','₺','₺ 0','(₺)','↗','↙','⇄','⌂','▤','▥','◷'}
 assert not [(a,c) for a,c in results if a==c and a not in allowed and not re.fullmatch(r'[\d\W]+',a)],[(a,c) for a,c in results if a==c and a not in allowed and not re.fullmatch(r'[\d\W]+',a)]
 page.locator('#open-privacy').click();assert 'How your data is processed' in page.locator('#legal-copy').inner_text();page.locator('#legal-close').click()
 # Menu switch back preserves both drafts and the Turkish UI.
 page.select_option('#language-select','tr');page.wait_for_timeout(100)
 assert page.locator('#unit-price').input_value()=='1.234,56'
 assert page.locator('[data-tab=home]').inner_text().strip().endswith('Ana Sayfa')
 page.select_option('#language-select','en');page.locator('#account-close').click()
 # English number entry saves canonical numeric values, not translated financial record identifiers.
 page.locator('#trade-submit').click();page.wait_for_timeout(300)
 d=page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1"))')
 tx=d['trades'][-1];assert tx['asset']=='Dolar' and tx['action']=='Alış' and tx['price']==1234.56 and tx['quantity']==12.5,tx
 # User-entered names are not translated even when they equal a UI label.
 page.locator('[data-tab=more]').click();assert page.locator('#rec-list [data-user-text]').inner_text()=='Gelir'
 page.locator('#account-open').click();assert page.locator('#asset-visibility-controls [data-user-text]').inner_text()=='Gider';page.locator('#account-close').click()
 # Async price notes and all selected asset branches.
 page.locator('[data-tab=trade]').click()
 for asset in ['Dolar','Euro','Pound','Gram altın','Gram gümüş','Vade Dışı TL Yatırımlarım','Eurobond $','Eurobond €']:
  page.select_option('#asset',asset);page.wait_for_timeout(150)
  text=page.locator('#trade-form').inner_text()
  assert not re.search('[çğıİöşüÇĞÖŞÜ]',text),(asset,text)
 # Date notes after data arrives.
 page.locator('[data-tab=term]').click();page.locator('#term-start').fill('2026-10-01');page.wait_for_timeout(150)
 assert 'Daily reference rate' in page.locator('#term-start-fx-note').inner_text()
 # Future OS notifications use the chosen language without depending on the legacy disabled preference.
 schedules=page.evaluate('Hesap.notificationSchedule("2026-10-28T12:00:00")')
 assert next(n for n in schedules if n['id'].startswith('monthly-'))['body'].startswith('Remember')
 assert next(n for n in schedules if n['id'].startswith('term-'))['body']=='Your fixed-term deposit matures today.'
 assert any(n['body']=='Your "Gelir" payment is due tomorrow!' for n in schedules)
 assert page.evaluate('nativeMessages.filter(m=>m.action==="schedule").at(-1).enabled') is True
 before_reschedule=page.evaluate('nativeMessages.filter(m=>m.action==="schedule").length')
 page.evaluate('Hesap.refreshNotifications(undefined,true)')
 assert page.evaluate('nativeMessages.filter(m=>m.action==="schedule").length')==before_reschedule+1
 page.locator('#notifications-open').click();assert page.evaluate('nativeMessages.some(m=>m.action==="requestPermission")')
 assert all(':' not in x for x in page.locator('#notification-list small').all_text_contents())
 page.locator('#notifications-close').click()
 # Language selection survives restart and appears in backups.
 page.reload();page.wait_for_timeout(350);assert page.evaluate('document.documentElement.lang')=='en-GB'
 page.locator('#account-open').click();page.locator('#backup-export').click()
 backup=page.evaluate('JSON.parse(nativeMessages.filter(m=>m.action==="export").at(-1).content)')
 assert backup['data']['language']=='en' and backup['data']['trades'][-1]['asset']=='Dolar'
 # Restore an old backup that disabled notifications: the inbox must still remain enabled.
 page.evaluate('(payload)=>window.dispatchEvent(new CustomEvent("hesap-native",{detail:{type:"import",payload}}))',{'application':'Hesap','version':1,'data':fixture})
 assert 'Restoring it will replace your current data' in page.locator('#restore-summary').inner_text()
 page.locator('#restore-confirm').click();page.wait_for_timeout(300)
 assert page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).notifications.enabled') is True
 assert page.locator('.notification-item').count()>0
 # Both languages and both themes fit typical iPhone widths.
 for language in ['en','tr']:
  page.locator('#account-open').click();page.select_option('#language-select',language);page.locator('#account-close').click()
  for width in [320,390,430]:
   page.set_viewport_size({'width':width,'height':844})
   for tab in ['home','trade','track','term','more','charts']:
    page.locator('[data-tab='+tab+']').click();page.wait_for_timeout(40)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(language,width,tab)
 assert not errors,errors
 print('PASS: static-copy coverage; draft-safe TR↔EN switching; canonical saved amounts/assets; custom names preserved; eight asset branches and async notes; translated notification payloads and permission bridge; preference persistence; backup/restore migration; 36 iPhone screen/locale checks; no JS errors.')
 b.close()
