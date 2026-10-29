from pathlib import Path
import shutil
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
s=(Path(__file__).resolve().parents[1]/'finans-ilk-prototip.html').read_text()
fixture={'trades':[{'id':'usd','asset':'Dolar','action':'Alış','date':'2026-01-01','quantity':100,'price':40},{'id':'eur','asset':'Euro','action':'Alış','date':'2026-01-01','quantity':100,'price':40},{'id':'gold','asset':'Gram altın','action':'Alış','date':'2026-01-01','quantity':10,'price':2500,'ounceUsd':2000},{'id':'silver','asset':'Gram gümüş','action':'Alış','date':'2026-01-01','quantity':100,'price':30,'ounceUsd':30}],'eurobond':{'usd':10,'eur':10}}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def net(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-01-01','average':2000}]})
 page.route('https://**/*',net);page.route('http://localhost/**',lambda r:r.fulfill(body=s,content_type='text/html'))
 page.goto('http://localhost/');page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',fixture);page.reload();page.wait_for_timeout(300);page.locator('[data-tab=charts]').click();page.wait_for_timeout(300)
 for lang in ['tr','en']:
  if lang=='en':page.locator('#account-open').click();page.select_option('#language-select','en');page.locator('#account-close').click();page.wait_for_timeout(200)
  text=page.locator('.allocation-totals').inner_text();assert ('Tüm Dolar' if lang=='tr' else 'Total USD') in text,text;assert ('Tüm Euro' if lang=='tr' else 'Total EUR') in text,text
  assert page.locator('.allocation-legend [data-user-text]').all_text_contents()==['gr','gr']
  for width in [320,390,430]:
   page.set_viewport_size({'width':width,'height':844})
   for theme in ['dark','light']:
    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
    ref=page.locator('.allocation-legend strong').first.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).color,getComputedStyle(e).fontWeight]')
    for entry in page.locator('.allocation-totals strong').all():assert entry.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).color,getComputedStyle(e).fontWeight]')==ref
    x=page.locator('.allocation-legend strong').first.bounding_box()['x']
    for row in page.locator('.allocation-total').all():
     title=row.locator('strong').first;amount=row.locator('small')
     assert row.locator('.allocation-total-content').evaluate('e=>[...e.children].map(x=>x.tagName)')==['STRONG','SMALL','STRONG']
     assert abs(title.bounding_box()['x']-x)<1
     assert amount.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).color]')==page.locator('.allocation-legend small').first.evaluate('e=>[getComputedStyle(e).fontSize,getComputedStyle(e).color]')
     assert abs(title.bounding_box()['y']-amount.bounding_box()['y'])<5,(width,lang,row.inner_text())
     assert row.locator('.allocation-total-dot').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')

 page.locator('[data-tab=trade]').click();page.wait_for_timeout(200)
 gaps=page.evaluate("()=>{const r=id=>document.getElementById(id).getBoundingClientRect();return [r('trade-month-field').top-r('trade-year').bottom,r('trade-year-summary').top-r('trade-month').bottom]}");assert abs(gaps[0]-14)<1 and abs(gaps[1]-16)<1,gaps
 assert not errors,errors
 b.close();print('PASS: portfolio label alignment, inline percentage/amount styles, white dots, euro USD equivalent and trade selector gaps across languages, widths and themes.')
