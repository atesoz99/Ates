from pathlib import Path
import shutil
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 browser_path=shutil.which('chromium') or shutil.which('google-chrome')
 b=p.chromium.launch(**({'executable_path':browser_path} if browser_path else {}),args=['--no-sandbox']);page=b.new_page(viewport={'width':320,'height':740},is_mobile=True,has_touch=True);page.clock.install(time=datetime(2026,10,28,12,tzinfo=timezone.utc))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('https://**/*',lambda r:r.abort())
 page.route('http://localhost/**',lambda r:r.fulfill(body=(ROOT/'finans-ilk-prototip.html').read_text(),content_type='text/html'))
 page.add_init_script('window.nativeMessages=[];window.webkit={messageHandlers:{hesap:{postMessage:m=>nativeMessages.push(m)}}};')
 page.goto('http://localhost/');page.wait_for_timeout(200);page.locator('#account-open').click();page.select_option('#language-select','en');page.locator('#account-close').click()
 for tab in ['home','trade','track','term','more','charts']:
  page.locator('[data-tab='+tab+']').click();page.wait_for_timeout(100)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  nodes=page.locator('#'+tab).evaluate('''root=>{const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),out=[];let n;while(n=w.nextNode()){if(/[çğıİöşüÇĞÖŞÜ]/.test(n.nodeValue))out.push(n.nodeValue)}return out;}''')
  assert not nodes,(tab,nodes)
 assert page.locator('#charts .empty-chart').count()==14
 page.locator('[data-tab=more]').click();page.locator('#recurring-submit').click()
 assert page.locator('#rec-name').evaluate('(e)=>e.validationMessage')=='Please complete this field.'
 page.locator('[data-tab=trade]').click();page.select_option('#asset','Eurobond $');page.locator('#other-tl-amount').fill('10');page.locator('#trade-submit').click();page.wait_for_timeout(100)
 assert page.locator('#toast').inner_text()=='The Eurobond amount cannot exceed your available USD cash.'
 page.select_option('#asset','Dolar');page.locator('#average-income-toggle').check();assert page.locator('#unit-price').evaluate('(e)=>e.readOnly')
 assert 'no existing holdings' in page.locator('#trade-price-note').inner_text()
 page.locator('[data-tab=term]').click();page.locator('#term-start').evaluate("(e)=>{e.value='2026-10-01';e.dispatchEvent(new Event('change',{bubbles:true}))}");page.wait_for_timeout(150)
 assert 'could not be retrieved' in page.locator('#term-start-fx-note').inner_text()
 page.locator('#account-open').click();before=page.evaluate('localStorage.getItem("finansim-prototype-v1")')
 page.locator('#backup-file').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'{bad json'})
 page.wait_for_timeout(100);assert 'valid JSON backup' in page.locator('#toast').inner_text();assert page.evaluate('localStorage.getItem("finansim-prototype-v1")')==before
 page.locator('#account-close').click();page.evaluate('window.dispatchEvent(new CustomEvent("hesap-native",{detail:{type:"permission",granted:false}}))');page.wait_for_timeout(100)
 assert page.locator('#toast').inner_text()=='Notifications are disabled in iOS. You can enable them in Settings.'
 assert page.locator('.notification-item').count()>0
 assert not errors,errors
 print('PASS: empty English screens, empty charts, English field validation, Eurobond errors, average-cost lock, offline rate errors, invalid JSON protection and denied OS permission with in-app inbox still active.')
 b.close()
