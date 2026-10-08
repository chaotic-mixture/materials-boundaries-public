"""Run against a local uvicorn instance on port 8765; no live query here."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).resolve().parents[1]/'evidence'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1365,'height':1050})
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8765')
 page.get_by_role('button',name='Load fixture demo').click()
 page.wait_for_selector('.card')
 assert 'FIXTURE DEMO' in page.locator('#status').inner_text()
 assert 'kg/m^3' in page.locator('.card').inner_text()
 page.locator('summary').click()
 assert 'structure_original' in page.locator('pre').inner_text()
 page.screenshot(path=str(out/'ui-nomad-fixture.png'),full_page=True)
 with page.expect_download() as download:
  page.get_by_role('button',name='Export current response JSON').click()
 download.value.save_as(out/'browser-export.json')
 assert json.loads((out/'browser-export.json').read_text())['page']['fixture'] is True
 page.locator('#provider').select_option('materials_project')
 page.get_by_role('button',name='Search public records').click()
 page.wait_for_function("document.querySelector('#status').textContent.includes('No authorized MP client')")
 assert page.locator('.card').count()==0
 page.get_by_role('button',name='Load fixture demo').click()
 page.wait_for_selector('.card')
 assert 'FIXTURE' in page.locator('.card').inner_text()
 page.get_by_role('button',name='Load fixture demo').click()
 page.wait_for_selector('.card')
 assert page.locator('.card').count()==1
 page.reload()
 assert page.locator('.card').count()==0
 page.set_viewport_size({'width':390,'height':844})
 page.get_by_role('button',name='Load fixture demo').click()
 page.wait_for_selector('.card')
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.screenshot(path=str(out/'ui-mobile-fixture.png'),full_page=True)
 assert not errors,errors
 browser.close()
(out/'browser-results.json').write_text(json.dumps({'status':'passed','browser':'system Chromium, Playwright 1.62.0', 'checks':['NOMAD replay labeled fixture','units and expanded provenance','JSON download','MP unavailable state','MP synthetic demo','repeated demo replaces results','reload clears response','390px responsive width','no page JS errors'],'live_query_in_this_test':False},indent=2)+'\n')
