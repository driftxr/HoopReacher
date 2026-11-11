import json
from bs4 import BeautifulSoup

def personalize(soup, rows, season):
    soup.body['class']=list(soup.body.get('class',[]))+['personal-picks']
    soup.title.string='Your NBA Standings'
    soup.select_one('h1').string='Your NBA Standings'
    header=soup.select_one('main > header')
    subtitle=soup.new_tag('p',attrs={'class':'intro'});subtitle.string=season.replace('-','/')+' Standings Picks';header.append(subtitle)
    for el in soup.select('.metrics, .conferences, main > section.notes'):el.decompose()
    container=BeautifulSoup('''<section id="personal-picks"><div class="pick-actions"><button id="export-picks" type="button">Export picks</button><button id="import-picks" type="button">Import picks</button><input id="pick-file" type="file" accept=".json,application/json" hidden></div><p id="pick-status" role="status" aria-live="polite">Choose your top 10 teams in each conference. Enable JavaScript to edit and save picks.</p><section class="metrics"><div><span>Exact positions</span><strong id="pick-matches">—</strong><small>of 20 predicted slots</small></div><div><span>Current match rate</span><strong id="pick-rate">—</strong><small id="pick-compared">No ranked picks yet</small></div><div><span>Your picks</span><strong id="pick-count">0 / 20</strong><small>One team per position</small></div></section><div class="conferences" id="pick-conferences"></div><p class="notes">Saved in this browser. Export a backup to move your picks to another device or recover them after closing this page. Scores compare your picks with the latest published standings.</p></section>''','html.parser').section
    header.insert_after(container)
    actions=container.select_one('.pick-actions').extract()
    container.select_one('p.notes').insert_before(actions)
    data=soup.new_tag('script',id='picks-data',type='application/json');data.string=json.dumps({'season':season,'teams':rows}).replace('<','\\u003c');soup.body.append(data)
    script=soup.new_tag('script',src='assets/picks.js',defer=True);soup.body.append(script)
