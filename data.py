"""ESPN data normalized for HoopReacher, with bounded persistent caching.

NBA team IDs remain stable so existing saved/imported picks stay compatible.
"""
import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from requests.exceptions import Timeout, ConnectionError

STANDINGS_TTL = 12 * 60 * 60
SCORES_TTL = 6 * 60 * 60
TEAM_LIST = json.loads(Path(__file__).with_name('teams.json').read_text())
TEAMS = {t['abbreviation']: t for t in TEAM_LIST}
BY_ID = {t['id']: t for t in TEAM_LIST}
BY_ESPN = {t['espn_id']: t for t in TEAM_LIST}
PICKS = {
    'East': [['DET'], ['PHI'], ['TOR'], ['NYK'], ['BOS'], ['IND'], ['MIA'], ['CLE','ORL','WAS']],
    'West': [['OKC'], ['SAS'], ['MIN'], ['DEN'], ['HOU'], ['LAL'], ['POR'], ['GSW','MEM','DAL']],
}
BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'


def number(value):
    if value in (None, '', '--', '—'): return None
    if isinstance(value, dict): value = value.get('value', value.get('displayValue'))
    if isinstance(value, str) and ':' in value:
        minutes, seconds = value.split(':')
        return float(minutes) + float(seconds) / 60
    return float(value)


def require(result):
    if result['error'] or result['data'] is None:
        raise ValueError('ESPN refresh incomplete; preserving previous publication')
    return result['data']

class Cache:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = str(path), clock
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, updated REAL, retry REAL)')

    def get(self, key, ttl, loader):
        with self.lock, sqlite3.connect(self.path) as db:
            now = self.clock()
            row = db.execute('SELECT value, updated, retry FROM cache WHERE key=?', (key,)).fetchone()
            value, updated, retry = row if row else (None, None, 0)
            stale = updated is None or now - updated >= ttl
            if stale and now >= retry:
                try:
                    for attempt in range(2):
                        try:
                            loaded = loader()
                            break
                        except (Timeout, ConnectionError):
                            if attempt == 1:
                                raise
                            logging.warning("Retrying ESPN request for %s", key)
                            time.sleep(5)
                    value = json.dumps(loaded, allow_nan=False)
                    updated, retry, stale = now, 0, False
                except Exception:
                    logging.exception('ESPN request failed for %s', key)
                    retry = now + 300
                db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)', (key, value, updated, retry))
            return {'data': json.loads(value) if value is not None else None,
                    'updated': updated, 'stale': stale,
                    'error': 'ESPN data is temporarily unavailable. Showing saved data where available.' if stale else None}

class NBA:
    def __init__(self, cache, season):
        self.cache, self.season = cache, season
        self.year = int(season[:4]) + 1
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'HoopReacher/1.0'

    def fetch(self, url, **params):
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def cached(self, key, ttl, loader):
        # Separate provider/version namespaces prevent mixing NBA and ESPN IDs.
        return self.cache.get(f'espn-v1:{self.season}:{key}', ttl, loader)

    def standings(self, phase):
        def load():
            data = self.fetch('https://site.api.espn.com/apis/v2/sports/basketball/nba/standings', season=self.year, seasontype=2)
            rows = []
            for conf in data['children']:
                if conf['abbreviation'] not in ('East', 'West'): continue
                table = conf['standings']
                if int(table['season']) != self.year or int(table['seasonType']) != 2:
                    raise ValueError('ESPN returned a different standings season')
                for entry in table['entries']:
                    t = BY_ESPN[entry['team']['id']]
                    stats = {s['name']: s.get('value') for s in entry['stats']}
                    rows.append(dict(TeamID=t['id'], TeamCity=t['city'], TeamName=t['nickname'],
                        Conference=conf['abbreviation'], PlayoffRank=int(stats['playoffSeed']),
                        WINS=int(stats['wins']), LOSSES=int(stats['losses']), WinPCT=stats['winPercent']))
            if len({r['TeamID'] for r in rows}) != 30:
                raise ValueError('ESPN returned incomplete standings')
            return rows
        return self.cached('standings', STANDINGS_TTL, load)

    def schedule(self):
        def load():
            games = {}
            for team in TEAM_LIST:
                data = self.fetch(BASE+f"teams/{team['espn_id']}/schedule", season=self.year, seasontype=2)
                if int(data['season']['year']) != self.year or int(data['season']['type']) != 2:
                    raise ValueError('ESPN returned a different schedule season')
                if not data.get('events'): raise ValueError('ESPN returned an empty team schedule')
                for event in data['events']:
                    if int(event['seasonType']['type']) != 2: continue
                    c = event['competitions'][0]
                    # Cup final does not count toward regular-season standings.
                    description = ' '.join(n.get('headline', n.get('text', '')) for n in c.get('notes', [])).lower()
                    if 'championship' in description and ('nba cup' in description or 'in-season' in description): continue
                    competitors = {p['homeAway']: p for p in c['competitors']}
                    h, a = competitors['home'], competitors['away']
                    home, away = BY_ESPN[h['id']], BY_ESPN[a['id']]
                    status = c['status']['type']
                    date = c.get('date', event['date'])
                    games[event['id']] = dict(gameId=event['id'], seasonType=2,
                        gameDateTimeUTC=date, gameDateEst=datetime.fromisoformat(date.replace('Z','+00:00')).astimezone(ZoneInfo('America/Toronto')).date().isoformat(),
                        gameStatus=3 if status.get('completed') else 2 if status['state']=='in' else 1,
                        gameStatusText=status.get('shortDetail',status['description']), isNeutral=c.get('neutralSite',False),
                        homeTeam_teamId=home['id'], awayTeam_teamId=away['id'],
                        homeTeam_teamTricode=home['abbreviation'], awayTeam_teamTricode=away['abbreviation'],
                        homeTeam_score=number(h.get('score')), awayTeam_score=number(a.get('score')))
            return sorted(games.values(), key=lambda g:(g['gameDateTimeUTC'],g['gameId']))
        return self.cached('schedule', SCORES_TTL, load)

    def roster(self, team):
        def load():
            data = self.fetch(BASE+f"teams/{BY_ID[team]['espn_id']}/roster", season=self.year)
            if int(data['season']['year']) != self.year: raise ValueError('Wrong roster season')
            rows = [dict(PLAYER_ID=int(p['id']), PLAYER=p['displayName'], NUM=p.get('jersey',''),
                         POSITION=p.get('position',{}).get('abbreviation','')) for p in data['athletes']]
            if not rows: raise ValueError('ESPN returned an empty roster')
            return rows
        return self.cached(f'roster:{team}', STANDINGS_TTL, load)

    def averages(self, team, phase):
        def load():
            totals = defaultdict(lambda: defaultdict(float))
            games = require(self.schedule())
            for game in games:
                if game['gameStatus'] != 3 or team not in (game['homeTeam_teamId'],game['awayTeam_teamId']): continue
                for p in require(self.game(game['gameId']))['players']:
                    if p['teamId'] != team or not p['played']: continue
                    total = totals[p['personId']]
                    total['GP'] += 1
                    for key in ('minutes','points','assists','reboundsTotal','steals','blocks','turnovers',
                                'fieldGoalsMade','fieldGoalsAttempted','threePointersMade','threePointersAttempted','freeThrowsMade','freeThrowsAttempted'):
                        if p[key] is None: raise ValueError('Incomplete played-player box score')
                        total[key] += p[key]
            rows = []
            for pid, total in totals.items():
                row = dict(PLAYER_ID=pid, GP=int(total['GP']))
                for key, source in {'MIN':'minutes','PTS':'points','AST':'assists','REB':'reboundsTotal','STL':'steals','BLK':'blocks','TOV':'turnovers'}.items():
                    row[key] = round(total[source]/total['GP'],1)
                for key, source in [('FG_PCT','fieldGoals'),('FG3_PCT','threePointers'),('FT_PCT','freeThrows')]:
                    attempts = total[source+'Attempted']
                    row[key] = total[source+'Made']/attempts if attempts else None
                rows.append(row)
            return rows
        return self.cached(f'averages:{team}', SCORES_TTL, load)

    def game(self, game_id):
        def load():
            data = self.fetch(BASE+'summary', event=game_id)
            competition = data['header']['competitions'][0]
            complete = competition['status']['type'].get('completed', False)
            box = data.get('boxscore', {})
            if complete and len(box.get('players', [])) != 2:
                raise ValueError('ESPN has not supplied a complete box score')
            scores = {p['id']: number(p.get('score')) for p in competition['competitors']}
            result = {'players': [], 'teams': []}
            for group in box.get('players', []):
                t = BY_ESPN[group['team']['id']]
                result['teams'].append(dict(teamId=t['id'],teamCity=t['city'],teamName=t['nickname'],points=scores[group['team']['id']]))
                for category in group['statistics']:
                    for athlete in category['athletes']:
                        p = athlete['athlete']; stats = dict(zip(category['labels'],athlete.get('stats',[])))
                        # ESPN occasionally marks a DNP false with MIN='--' and all-zero stats.
                        played = not athlete.get('didNotPlay',False) and bool(stats) and number(stats.get('MIN')) is not None
                        if not athlete.get('didNotPlay',False) and number(stats.get('MIN')) is None and any(number(stats.get(k)) not in (None,0) for k in ('PTS','REB','AST','STL','BLK')):
                            raise ValueError('Missing minutes for a played athlete')
                        row = dict(personId=int(p['id']), teamId=t['id'], firstName=p['displayName'], familyName='',
                            position=p.get('position',{}).get('abbreviation','G') if athlete.get('starter') else '',
                            played=played, comment=athlete.get('reason','DNP') if not played else '')
                        for label,key in [('MIN','minutes'),('PTS','points'),('REB','reboundsTotal'),('AST','assists'),('STL','steals'),('BLK','blocks'),('TO','turnovers')]:
                            row[key] = number(stats.get(label))
                        for label,key in [('FG','fieldGoals'),('3PT','threePointers'),('FT','freeThrows')]:
                            values = stats.get(label, '').split('-')
                            made, attempted = map(number,values) if len(values)==2 else (None,None)
                            row[key+'Made'],row[key+'Attempted'] = made,attempted
                            row[key+'Percentage'] = made/attempted if attempted else None
                        result['players'].append(row)
            return result
        return self.cached(f'game:{game_id}', SCORES_TTL, load)
