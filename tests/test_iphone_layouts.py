"""Representative iPhone portrait viewports, safe areas, both themes/languages, all screens."""
from pathlib import Path
from datetime import datetime,timezone
import shutil,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'finans-ilk-prototip.html').read_text()
fixture={'capital':[{'id':'old','date':'2025-12-01','amount':1000000,'fxRate':40},{'id':'a','date':'2026-01-01','amount':2000000,'fxRate':40},{'id':'b','date':'2026-10-01','amount':3000000,'fxRate':40}], 'budgets':[{'id':'a','month':'2026-09','income':100000,'expense':50000},{'id':'b','month':'2026-10','income':120000,'expense':60000}],'dailyGoal':1000,'trades':[{'id':'usd','asset':'Dolar','action':'Alış','date':'2026-01-01','quantity':60000,'price':40},{'id':'eur','asset':'Euro','action':'Alış','date':'2026-01-01','quantity':10000,'price':40},{'id':'gold','asset':'Gram altın','action':'Alış','date':'2026-01-01','quantity':100,'price':2500,'ounceUsd':2000}],'eurobond':{'usd':10000,'eur':1000},'terms':[{'id':'t','start':'2026-10-01','tryEnd':'2027-01-01','principal':100000,'income':10000,'startFx':40}],'recurring':[{'id':'p','name':'Telefon faturası','day':30,'amount':1000}]}
models=[('SE-1',320,568,20,0),('SE-2-3',375,667,20,0),('mini',375,812,50,34),('12-13-14',390,844,47,34),('14-15-Pro',393,852,59,34),('16-Pro',402,874,62,34),('11-Pro-Max',414,896,44,34),('12-13-Pro-Max',428,926,47,34),('14-15-Pro-Max',430,932,59,34),('16-Pro-Max',440,956,62,34)]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(is_mobile=True,has_touch=True);page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def net(r):
  if 'frankfurter' in r.request.url:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40}})
  elif '/spot/latest' in r.request.url:r.fulfill(json={'metals':{'gold':{'units':{'troyOunce':2500}},'silver':{'units':{'troyOunce':30}}}})
  else:r.fulfill(json={'data':[{'date':'2026-01-01','average':2000}]})
 page.route('https://**/*',net);page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'));page.goto('http://localhost/')
 checked=0
 for model,width,height,top,bottom in models:
  page.set_viewport_size({'width':width,'height':height})
  for language in ['tr','en']:
   for theme in ['light','dark']:
    d={**fixture,'theme':theme,'language':language};page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',d);page.reload();page.wait_for_timeout(60)
    page.add_style_tag(content=f'.app{{padding-top:{top}px!important;padding-bottom:{92+bottom}px!important}}.tabs{{padding-bottom:{bottom}px!important}}')
    for screen in ['home','trade','track','term','more','charts']:
     page.locator('[data-tab='+screen+']').evaluate('e=>e.click()');page.wait_for_timeout(20)
     overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
     assert overflow<=1,(model,language,theme,screen,overflow)
     clipped=page.locator('#'+screen+' input:not([type=hidden]),#'+screen+' select,#'+screen+' button.primary').evaluate_all('es=>es.filter(e=>e.getClientRects().length).map(e=>({id:e.id,x:e.getBoundingClientRect().x,right:e.getBoundingClientRect().right})).filter(r=>r.x<0||r.right>innerWidth+1)')
     assert not clipped,(model,language,theme,screen,clipped)
     checked+=1
 # The widget layout preview uses the same font sizes, colours and padding as the native source.
 page.set_content((ROOT/'ios-widget/Onizleme.html').read_text())
 for id in ['tr-widget','en-widget']:
  for width in [292,320,338,360]:
   page.locator('#'+id).evaluate('(e,w)=>e.style.width=w+"px"',width)
   assert page.locator('#'+id).evaluate('e=>e.scrollHeight<=e.clientHeight && e.scrollWidth<=e.clientWidth'),(id,width)
 for id in ['tr-widget','en-widget']:
  page.locator('#'+id).evaluate('e=>{e.style.width="292px";e.style.height="141px";e.style.padding="10px"}')
  assert page.locator('#'+id).evaluate('e=>e.scrollHeight<=e.clientHeight && e.scrollWidth<=e.clientWidth'),id
 # Show why the medium-only choice preserves the typography.
 page.locator('#tr-widget').evaluate('e=>e.style.width="155px"')
 assert page.locator('#tr-widget').evaluate('e=>e.scrollHeight>e.clientHeight')
 assert not errors,errors
 b.close();print(f'PASS: {checked} iPhone screen/locale/theme cases with simulated safe areas; medium widget preview fits 292–360px; smallest layout cannot retain all copy at the same sizes.')
