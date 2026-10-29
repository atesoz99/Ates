from pathlib import Path
from datetime import datetime,timezone
import shutil
from playwright.sync_api import sync_playwright
source=(Path(__file__).resolve().parents[1]/'finans-ilk-prototip.html').read_text()
data={'trades':[{'id':'a','asset':'Dolar','action':'Alış','date':'2026-01-01','quantity':60,'price':40},{'id':'b','asset':'Dolar','action':'Alış','date':'2026-02-01','quantity':40,'price':40},{'id':'s','asset':'Dolar','action':'Satış','date':'2026-01-20','quantity':10},{'id':'m','asset':'Dolar','action':'Satış','date':'2026-03-01','quantity':5}]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});page.clock.install(time=datetime(2026,10,29,12,tzinfo=timezone.utc))
 page.route('http://localhost/**',lambda r:r.fulfill(body=source,content_type='text/html'));page.route('https://**/*',lambda r:r.fulfill(json={'date':'2026-10-29','rates':{'TRY':40}}))
 page.goto('http://localhost/');page.evaluate('(d)=>localStorage.setItem("finansim-prototype-v1",JSON.stringify(d))',data);page.reload();page.wait_for_timeout(200);page.locator('[data-tab=trade]').click()
 for language in ['tr','en']:
  if language=='en':page.locator('#account-open').click();page.select_option('#language-select','en');page.locator('#account-close').click()
  for month,expected in [('all','85'),('1','50'),('2','40'),('3','-5'),('4','0')]:
   page.select_option('#trade-month',month);page.wait_for_timeout(50)
   block=page.locator('#trade-year-summary .trade-card .small').first
   assert block.inner_text().splitlines()[-1]=='Net: '+expected+' $',block.inner_text()
   structure=block.evaluate('''e=>{const result=[];for(const n of e.childNodes){if(n.nodeType===Node.TEXT_NODE){const r=document.createRange();r.selectNodeContents(n);result.push({text:n.textContent.trim(),y:r.getBoundingClientRect().top})}}return result.filter(x=>x.text)}''')
   assert len(structure)==3,structure
   assert abs((structure[1]['y']-structure[0]['y'])-(structure[2]['y']-structure[1]['y']))<1,structure
   assert block.locator('br').count()==2
 b.close();print('PASS: Net in both languages; full-year/month positive, negative and zero results; equal Alış/Satış/Net line spacing and shared typography.')
