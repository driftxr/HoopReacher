import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, abort, render_template, request
from data import NBA, Cache, PICKS, TEAMS, BY_ID, STANDINGS_TTL, SCORES_TTL

EASTERN = ZoneInfo('America/Toronto')

def prediction_rows(raw):
    standings = {r['TeamID']: r for r in raw}
    conferences, matches, compared = {}, 0, 0
    for conference, picks in PICKS.items():
        rows = []
        for position, options in enumerate(picks, 1):
            slot_ranks = []
            for abbr in options:
                team = TEAMS[abbr]
                current = standings.get(team['id'], {})
                played = current.get('WINS', 0) + current.get('LOSSES', 0) > 0
                rank = current.get('PlayoffRank') if played else None
                rank = rank if isinstance(rank, (int, float)) and 1 <= rank <= 15 else None
                slot_ranks.append(rank)
                rows.append(dict(pick=position, abbr=abbr, name=team['full_name'], rank=rank,
                    wins=current.get('WINS'), losses=current.get('LOSSES'), pct=current.get('WinPCT'),
                    gap=rank-position if rank is not None else None))
            if all(rank is not None for rank in slot_ranks):
                compared += 1
                matches += int(position in slot_ranks)
        conferences[conference] = rows
    return conferences, matches, compared

def create_app(nba=None):
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    season = os.getenv('NBA_SEASON', '2026-27')
    if not re.fullmatch(r'\d{4}-\d{2}', season):
        raise ValueError('NBA_SEASON must look like 2026-27')
    nba = nba or NBA(Cache(os.getenv('NBA_CACHE', str(Path(__file__).parent/'instance'/'nba.sqlite3'))), season)
    app.extensions['nba'] = nba

    @app.template_filter('number')
    def number(value):
        return '—' if value is None else f'{value:g}' if isinstance(value, (float,int)) else value

    @app.template_filter('percent')
    def percent(value):
        return '—' if value is None else f'{value*100:.1f}%'

    @app.template_filter('eastern')
    def eastern(value):
        if not value:
            return 'Time TBD'
        try:
            dt = datetime.fromisoformat(value.replace('Z','+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            return dt.astimezone(EASTERN).strftime('%b %d, %Y · %I:%M %p %Z')
        except ValueError:
            return value

    def phase():
        return 'Regular Season'

    def page(template, title, results=(), interval=SCORES_TTL, **context):
        stamps = [r['updated'] for r in results if r['updated'] is not None]
        updated = datetime.fromtimestamp(min(stamps), EASTERN).strftime('%b %d, %Y · %I:%M %p %Z') if stamps else None
        return render_template(template, title=title, season=season, phase=phase(),
            errors=list(dict.fromkeys(r['error'] for r in results if r.get('error'))),
            updated=updated, interval=interval, **context)

    @app.get('/')
    def home():
        result = nba.standings(phase())
        conferences, matches, compared = prediction_rows(result['data'] or [])
        sort = request.args.get('sort','pick')
        if sort not in ('pick','name','rank','wins','pct','gap'):
            sort = 'pick'
        reverse = request.args.get('direction') == 'desc'
        for rows in conferences.values():
            rows.sort(key=lambda row: row[sort] if row[sort] is not None else 0, reverse=reverse)
            rows.sort(key=lambda row: row[sort] is None)
        return page('home.html','NBA '+season+' Predictions',[result],STANDINGS_TTL,
            conferences=conferences,matches=matches,compared=compared,sort=sort,
            direction='desc' if reverse else 'asc')

    @app.get('/standings')
    def standings():
        result=nba.standings(phase())
        conferences={name: sorted([r for r in result['data'] or [] if r['Conference']==name],key=lambda r:r['PlayoffRank']) for name in ('East','West')}
        return page('standings.html','Current Standings',[result],STANDINGS_TTL,conferences=conferences,teams=BY_ID)

    def games_for_phase(rows):
        # NBA game ID prefixes: 001 preseason, 002 regular season; omit playoffs and Cup final.
        prefix='002'
        return [r for r in rows if str(r['gameId']).startswith(prefix)]

    @app.get('/today')
    def today():
        date=request.args.get('date',datetime.now(EASTERN).date().isoformat())
        try:
            datetime.strptime(date,'%Y-%m-%d')
        except ValueError:
            abort(400)
        result=nba.schedule()
        games=[g for g in games_for_phase(result['data'] or []) if str(g.get('gameDateEst',''))[:10]==date]
        return page('schedule.html',"Daily Schedule",[result],games=games,date=date,team=None)

    @app.get('/team/<abbr>')
    def team(abbr):
        if abbr not in TEAMS:
            abort(404)
        team=TEAMS[abbr]
        view=request.args.get('view','roster')
        if view=='schedule':
            result=nba.schedule()
            games=[g for g in games_for_phase(result['data'] or []) if team['id'] in (g['homeTeam_teamId'],g['awayTeam_teamId'])]
            mode=request.args.get('filter','all')
            games=[g for g in games if mode=='all' or (mode=='completed' and g['gameStatus']==3) or (mode=='upcoming' and g['gameStatus']!=3)]
            return page('schedule.html',team['full_name']+' Schedule',[result],games=games,team=team,date=None)
        roster, stats=nba.roster(team['id']),nba.averages(team['id'],phase())
        averages={p['PLAYER_ID']:p for p in stats['data'] or []}
        players=[dict(p, stats=averages.get(p['PLAYER_ID'],{})) for p in roster['data'] or []]
        sort=request.args.get('sort','STARTERS')
        results=[roster,stats]
        lineup_note=None
        columns=('NUM','PLAYER','GP','MIN','PTS','AST','REB','FG_PCT','FG3_PCT','FT_PCT','STL','BLK','TOV')
        direction=request.args.get('direction','asc' if sort in ('NUM','PLAYER') else 'desc')
        direction='asc' if direction=='asc' else 'desc'
        if sort not in columns:
            sort='STARTERS'
            schedule=nba.schedule()
            results.append(schedule)
            completed=[g for g in games_for_phase(schedule['data'] or [])
                if g['gameStatus']==3 and team['id'] in (g['homeTeam_teamId'],g['awayTeam_teamId'])]
            completed.sort(key=lambda g:g.get('gameDateTimeUTC') or g.get('gameDateEst') or '', reverse=True)
            starters=set()
            if completed:
                latest=completed[0]
                box=nba.game(latest['gameId'])
                results.append(box)
                starters={p['personId'] for p in (box['data'] or {}).get('players',[])
                    if p.get('teamId')==team['id'] and (p.get('position') or '').strip()}
                roster_ids={p['PLAYER_ID'] for p in players}
                if len(starters)==5 and starters <= roster_ids:
                    lineup_note='Starting five from the latest completed game ('+str(latest.get('gameDateEst',''))[:10]+'); bench ordered by minutes per game.'
                else:
                    starters=set()
            if not starters:
                lineup_note='Starting five unavailable for the current roster. Players are ordered by minutes per game.'
            players.sort(key=lambda p:(p['PLAYER_ID'] not in starters,
                -(p['stats'].get('MIN') or 0), p['PLAYER']))
        else:
            def sort_value(player):
                if sort=='PLAYER':
                    return player['PLAYER'].casefold()
                if sort=='NUM':
                    number=str(player.get('NUM') or '')
                    return int(number) if number.isdigit() else None
                return player['stats'].get(sort)
            players.sort(key=lambda p:p['PLAYER'].casefold())
            players.sort(key=lambda p:sort_value(p) if sort_value(p) is not None else 0,
                reverse=direction=='desc')
            players.sort(key=lambda p:sort_value(p) is None)
        return page('roster.html',team['full_name'],results,team=team,players=players,
            roster_sort=sort,roster_direction=direction)

    @app.get('/game/<game_id>')
    def game(game_id):
        if not re.fullmatch(r'002\d{7}',game_id):
            abort(404)
        result=nba.game(game_id)
        data=result['data'] or {'players':[],'teams':[]}
        return page('game.html','Game Stats',[result],game=data)

    @app.get('/health')
    def health():
        return {'status':'ok','season':season}

    return app

if __name__=='__main__':
    from waitress import serve
    serve(create_app(), host=os.getenv('HOST','127.0.0.1'), port=int(os.getenv('PORT','8000')))
