"""Generate a portable static site: python export_static.py --output dist."""
import argparse
import json
import os
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode
from bs4 import BeautifulSoup
from flask import render_template
from app import create_app, EASTERN
from personalize import personalize
from data import NBA, Cache, TEAMS

ROOT=Path(__file__).parent

def filename(path, query):
    if path=='/': return 'index.html'
    if path in ('/standings','/today'): return path[1:]+'.html'
    if path.startswith('/team/'):
        return 'team-'+path.split('/')[-1]+('-schedule' if query.get('view',[''])[0]=='schedule' else '')+'.html'
    if path.startswith('/game/'): return 'game-'+path.split('/')[-1]+'.html'
    if path.startswith('/static/'): return 'assets/'+path.split('/')[-1]
    raise ValueError('Unmapped local URL: '+path)

class Snapshot:
    def __init__(self,nba):
        self.nba=nba; self.memo={}; self.warnings=[]
    def call(self,name,*args):
        key=(name,*args)
        if key not in self.memo:
            result=getattr(self.nba,name)(*args)
            if result['data'] is None: raise RuntimeError(f'Missing {key}; export stopped to preserve previous site')
            if result.get('error'): raise RuntimeError(f'ESPN refresh failed for {key}; keeping the previously published site')
            self.memo[key]=result
        return self.memo[key]
    def standings(self,*a):return self.call('standings',*a)
    def schedule(self,*a):return self.call('schedule',*a)
    def roster(self,*a):return self.call('roster',*a)
    def averages(self,*a):return self.call('averages',*a)
    def game(self,*a):return self.call('game',*a)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='dist');parser.add_argument('--refresh',action='store_true',help='Refresh all ESPN data for this publication');args=parser.parse_args()
    target=Path(args.output).resolve();stage=target.with_name(target.name+'-building')
    stage.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'static',stage/'assets',dirs_exist_ok=True)
    cache=Cache(os.getenv('NBA_CACHE',str(ROOT/'instance/nba.sqlite3')))
    if args.refresh:
        # Each publishing run gets fresh data even if the previous run started late.
        with sqlite3.connect(cache.path) as db:
            db.execute("UPDATE cache SET updated=NULL, retry=0 WHERE key LIKE 'espn-%'")
    source=Snapshot(NBA(cache,os.getenv('NBA_SEASON','2026-27')))
    app=create_app(source);client=app.test_client()
    source.standings('Regular Season')
    games=[g for g in source.schedule()['data'] if g.get('seasonType') == 2]
    by_game={g['gameId']:g for g in games}
    # Future games have no box score to retrieve yet.
    for game in games:
        if game['gameStatus']==1:
            source.memo[('game',game['gameId'])]=dict(data={'players':[],'teams':[]},updated=None,error=None)
    built=datetime.now(EASTERN).isoformat()
    count=0

    def save(url, html=None, daily_games=None):
        nonlocal count
        if html is None:
            response=client.get(url)
            if response.status_code!=200:raise RuntimeError(f'{url}: {response.status_code}')
            html=response.data.decode()
        soup=BeautifulSoup(html,'html.parser')
        for meta in soup.select('meta[http-equiv="refresh"]'):meta.decompose()
        for element in soup.select('[href], [src]'):
            attr='href' if element.has_attr('href') else 'src';link=element[attr]
            if not link.startswith('/'):continue
            parsed=urlsplit(link);q=parse_qs(parsed.query);dest=filename(parsed.path,q)
            for key in ('view','sort','direction'):q.pop(key,None)
            element[attr]=dest+('?' + urlencode(q,doseq=True) if q else '')
        # Header links become browser-side sorts, preserving the default DOM order.
        for table in soup.select('table'):
            for index,th in enumerate(table.select('thead th')):
                link=th.select_one('a.roster-column-sort')
                if link:
                    button=soup.new_tag('button',type='button');button['class']='static-sort';button['data-column']=str(index)
                    button['data-default']='asc' if index in (0,1) else 'desc'
                    button['aria-label']='Sort '+link.get_text(' ',strip=True).rstrip('↑↓↕ ')
                    button.extend(list(link.contents));link.replace_with(button)
        if daily_games is not None:
            rows=soup.select('tbody tr')
            for row,g in zip(rows,daily_games):
                row['data-date']=str(g['gameDateEst'])[:10];row['data-status']=str(g['gameStatus'])
        elif '?view=schedule' in url:
            abbr=url.split('/team/')[1].split('?')[0];team_id=TEAMS[abbr]['id']
            selected=[g for g in games if team_id in (g['homeTeam_teamId'],g['awayTeam_teamId'])]
            for row,g in zip(soup.select('tbody tr'),selected):row['data-status']=str(g['gameStatus'])
        for field in soup.select('input[name="back"], input[name="view"]'):field.decompose()
        footer=soup.select_one('footer.notes')
        if footer:
            p=footer.find('p');p.clear();p.append('Source: ESPN. Updates are scheduled hourly; published data may lag live games.')
        script=soup.new_tag('script',src='assets/static-site.js',defer=True);soup.body.append(script)
        for style in soup.select('link[rel="stylesheet"]'):style['href']='assets/style.css'
        if daily_games is not None:soup.body['data-page']='daily'
        if url.startswith('/team/'):soup.body['data-page']='team'
        if url=='/standings': soup.body['data-page']='standings'
        if url=='/': personalize(soup, source.standings('Regular Season')['data'], source.nba.season)
        parsed=urlsplit(url);name=filename(parsed.path,parse_qs(parsed.query))
        (stage/name).write_text(str(soup));count+=1
        if count%25==0:print(f'Generated {count} pages',flush=True)

    save('/');save('/standings')
    with app.test_request_context('/today'):
        daily=render_template('schedule.html',title='Daily Schedule',season=source.nba.season,phase='Regular Season',errors=[],updated=datetime.fromtimestamp(source.schedule()['updated'],EASTERN).strftime('%b %d, %Y · %I:%M %p %Z'),interval=3600,games=games,date=datetime.now(EASTERN).date().isoformat(),team=None)
    save('/today',daily,games)
    for abbr in TEAMS:
        print('Exporting '+abbr,flush=True)
        save('/team/'+abbr);save('/team/'+abbr+'?view=schedule')
    for g in games:save('/game/'+g['gameId'])
    (stage/'.nojekyll').touch()
    if (ROOT/'CNAME').is_file(): shutil.copy(ROOT/'CNAME',stage/'CNAME')
    (stage/'export-info.json').write_text(json.dumps(dict(built=built,pages=count,season=source.nba.season,stale_sources=source.warnings),indent=2))
    # All assets and internal destinations must exist, including under a GitHub project URL.
    for path in stage.glob('*.html'):
        soup=BeautifulSoup(path.read_text(),'html.parser')
        for e in soup.select('[href], [src]'):
            link=e.get('href',e.get('src'));u=urlsplit(link)
            if u.scheme or not u.path:continue
            if not (stage/u.path).is_file():raise RuntimeError(f'Broken link in {path.name}: {link}')
    target.mkdir(parents=True,exist_ok=True)
    shutil.copytree(stage,target,dirs_exist_ok=True)
    print(f'Export complete: {count} pages in {target}; stale sources: {len(source.warnings)}',flush=True)

if __name__=='__main__':main()
