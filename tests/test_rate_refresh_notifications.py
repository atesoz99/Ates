"""Minute refresh, midnight rollover, preserved drafts/rates, and inbox destinations."""
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'finans-ilk-prototip.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844})
 page.clock.install(time=datetime(2026,10,29,23,59,30,tzinfo=timezone.utc))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 state={'rate':40,'date':'2026-10-29','requests':0,'offline':False}
 def net(r):
  state['requests']+=1
  if state['offline']:r.abort();return
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':state['date'],'rates':{'TRY':state['rate']}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-10-29','average':2500}]})
 page.route('https://**/*',net);page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'))
 page.add_init_script('''window.messages=[];window.webkit={messageHandlers:{hesap:{postMessage:m=>messages.push(m)}}};
 if(!localStorage.getItem('finansim-prototype-v1'))localStorage.setItem('finansim-prototype-v1',JSON.stringify({trades:[{id:'usd',asset:'Dolar',action:'Alış',date:'2026-01-01',quantity:100,price:30}],capital:[{id:'cap',date:'2026-10-01',amount:100000,fxRate:35,fxDate:'2026-10-20'}],recurring:[{id:'rent',name:'Kira',day:31,amount:5000}]}));''')
 page.goto('http://localhost/');page.wait_for_timeout(200)
 page.locator('[data-tab=trade]').click();page.wait_for_timeout(150)
 assert '29/10/2026' in page.locator('#trade-price-note').inner_text()
 page.locator('#quantity').fill('12.345');page.locator('#quantity').evaluate('e=>e.blur()')
 page.locator('#track-income').evaluate("e=>e.value='7.777'")
 before=state['requests'];state.update(rate=41,date='2026-10-30')
 # One minute also crosses midnight, without reopening the app.
 page.clock.run_for(60000);page.wait_for_timeout(300)
 assert state['requests']>before
 assert page.locator('#trade-date').input_value()=='2026-10-30'
 assert '30/10/2026' in page.locator('#trade-price-note').inner_text()
 assert page.locator('#unit-price').input_value()=='41,00'
 assert page.locator('#quantity').input_value()=='12.345'
 assert '1.100' in page.locator('#trade-summary').inner_text()
 assert page.locator('#track-income').input_value()=='7.777'
 assert page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).capital[0].fxRate')==35
 page.locator('#unit-price').fill('37,25');state['rate']=42
 page.clock.run_for(60000);page.wait_for_timeout(250)
 assert page.locator('#unit-price').input_value()=='37,25'
 state['offline']=True;page.clock.run_for(60000);page.wait_for_timeout(200)
 assert page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1")).cachedRate')==42
 assert '1.200' in page.locator('#trade-summary').inner_text()
 assert page.locator('#unit-price').input_value()=='37,25'
 state['offline']=False
 # A newly due payment makes the bell dot appear before opening the inbox.
 page.clock.set_fixed_time(datetime(2026,10,30,10,1,tzinfo=timezone.utc));page.evaluate('window.Hesap.refreshNotifications()')
 assert page.locator('#notification-dot').is_visible()
 page.locator('#notifications-open').click();page.wait_for_timeout(100)
 assert not page.locator('#notification-dot').is_visible()
 assert page.locator('.notification-delete').first.evaluate('e=>getComputedStyle(e).fontSize')==page.locator('#notifications-clear').evaluate('e=>getComputedStyle(e).fontSize')
 page.locator('[data-open-notice^="payment-"]').first.click();page.wait_for_timeout(100)
 assert page.locator('#more').evaluate('e=>e.classList.contains("active")')
 assert page.locator('#notifications-overlay').is_hidden()
 page.locator('#notifications-open').click();page.locator('[data-open-notice^="monthly-"]').first.click();page.wait_for_timeout(100)
 assert page.locator('#track').evaluate('e=>e.classList.contains("active")')
 assert page.locator('#capital-date').input_value()=='2026-10'
 # Same routing API is used by native lock-screen notification taps.
 page.evaluate('window.Hesap.openNotification("payment-rent-2026-10-31")');page.wait_for_timeout(100)
 assert page.locator('#more').evaluate('e=>e.classList.contains("active")')
 assert not errors,errors
 b.close();print('PASS: minute/midnight refresh, manual drafts and historical rates retained, unread dot, matching delete sizes, inbox/native routes.')
