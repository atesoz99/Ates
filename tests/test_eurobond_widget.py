"""Buy deletion invariants, hidden asset allocations, and widget snapshot bridge."""
from pathlib import Path
from datetime import datetime,timezone
import shutil,copy
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'finans-ilk-prototip.html').read_text()
fixture={'trades':[{'id':'usd-old','asset':'Dolar','action':'Alış','date':'2026-01-01','quantity':60,'price':40},{'id':'usd-new','asset':'Dolar','action':'Alış','date':'2026-02-01','quantity':40,'price':40},{'id':'eur-old','asset':'Euro','action':'Alış','date':'2026-01-01','quantity':60,'price':40},{'id':'eur-new','asset':'Euro','action':'Alış','date':'2026-02-01','quantity':40,'price':40}], 'eurobond':{'usd':80,'eur':80},'dailyGoal':1000}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844})
 page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def net(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-01-01','average':2000}]})
 page.route('https://**/*',net);page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'))
 page.add_init_script('window.nativeMessages=[];window.webkit={messageHandlers:{hesap:{postMessage:m=>nativeMessages.push(m)}}};')
 page.goto('http://localhost/');page.wait_for_timeout(150)
 def load(data):
  page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',data);page.reload();page.wait_for_timeout(150);page.locator('[data-tab=trade]').click();page.wait_for_timeout(100)
 def read():return page.evaluate('JSON.parse(localStorage.getItem("finansim-prototype-v1"))')
 load(fixture)
 assert page.evaluate('nativeMessages.filter(m=>m.action==="widgetSnapshot").at(-1)')=={'action':'widgetSnapshot','dailyGoal':1000,'language':'tr'}
 page.locator('[data-delete=trades][data-id=usd-old]').click();page.wait_for_timeout(100)
 assert read()['eurobond']=={'usd':0,'eur':80}
 page.locator('[data-delete=trades][data-id=eur-old]').click();page.wait_for_timeout(100)
 assert read()['eurobond']=={'usd':0,'eur':0}
 assert page.locator('#toast').inner_text()=='Kayıt silindi'
 exact=copy.deepcopy(fixture);exact['eurobond']={'usd':40,'eur':100};load(exact)
 page.locator('[data-delete=trades][data-id=usd-old]').click();page.wait_for_timeout(100)
 assert read()['eurobond']=={'usd':40,'eur':100}
 fractional=copy.deepcopy(fixture);fractional['trades'][0]['quantity']=0.1;fractional['trades'][1]['quantity']=0.2;fractional['trades'].append({'id':'usd-last','asset':'Dolar','action':'Alış','date':'2026-03-01','quantity':0.3,'price':40});fractional['eurobond']['usd']=0.3;load(fractional)
 page.locator('[data-delete=trades][data-id=usd-last]').click();page.wait_for_timeout(100)
 assert read()['eurobond']['usd']==0.3
 hidden=copy.deepcopy(fixture);hidden['hiddenTradeAssets']=['Dolar','Euro','Gram altın','Gram gümüş','Pound','Eurobond $','Eurobond €','Vade Dışı TL Yatırımlarım'];hidden['trades'].append({'id':'gold','asset':'Gram altın','action':'Alış','date':'2026-03-01','quantity':10,'price':2500,'ounceUsd':2000});load(hidden)
 page.locator('[data-tab=charts]').click();page.wait_for_timeout(200)
 text=page.locator('#graph-asset-allocation').inner_text()
 assert 'Eurobond $' in text and 'Eurobond €' in text and 'Gram Altın' in text,text
 # Widget receives saved target and language only, without financial record arrays.
 page.locator('[data-tab=home]').click();page.locator('#daily-goal-home').fill('2.500');page.locator('#daily-goal-form button').click();page.wait_for_timeout(100)
 message=page.evaluate('nativeMessages.filter(m=>m.action==="widgetSnapshot").at(-1)')
 assert message=={'action':'widgetSnapshot','dailyGoal':2500,'language':'tr'},message
 assert '72.500' in page.locator('#daily-target').inner_text()
 count=page.evaluate('nativeMessages.filter(m=>m.action==="widgetSnapshot").length')
 page.locator('[data-tab=trade]').click();page.locator('#account-open').click();page.wait_for_timeout(100)
 assert page.evaluate('nativeMessages.filter(m=>m.action==="widgetSnapshot").length')==count
 page.select_option('#language-select','en');page.wait_for_timeout(100)
 assert page.evaluate('nativeMessages.filter(m=>m.action==="widgetSnapshot").at(-1).language')=='en'
 page.clock.set_fixed_time(datetime(2026,11,1,12,tzinfo=timezone.utc));page.evaluate('window.Hesap.refreshSpendingTarget()');page.wait_for_timeout(80)
 page.locator('#account-close').click();page.locator('[data-tab=home]').click();page.wait_for_timeout(100)
 assert '2,500' in page.locator('#daily-target').inner_text()
 assert 'Day 1 of the month'==page.locator('#day-label').inner_text()
 assert not errors,errors
 b.close();print('PASS: USD/EUR Eurobond deletion, currency isolation, exact/fractional coverage retained, hidden holdings still charted, widget target/language-only snapshot and reload deduplication.')
