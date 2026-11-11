"""NBA.com access through nba_api, with persistent, bounded-refresh caching."""
import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from requests.exceptions import Timeout, ConnectionError
from nba_api.stats.static import teams
from nba_api.stats.endpoints import (leaguestandingsv3, scheduleleaguev2,
    commonteamroster, leaguedashplayerstats, boxscoretraditionalv3)

STANDINGS_TTL = 12 * 60 * 60
SCORES_TTL = 6 * 60 * 60
TEAM_LIST = teams.get_teams()
TEAMS = {t['abbreviation']: t for t in TEAM_LIST}
BY_ID = {t['id']: t for t in TEAM_LIST}
PICKS = {
    'East': [['DET'], ['PHI'], ['TOR'], ['NYK'], ['BOS'], ['IND'], ['MIA'], ['CLE','ORL','WAS']],
    'West': [['OKC'], ['SAS'], ['MIN'], ['DEN'], ['HOU'], ['LAL'], ['POR'], ['GSW','MEM','DAL']],
}

def records(dataset):
    value = dataset.get_dict()
    return [dict(zip(value['headers'], row)) for row in value['data']]

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
                            logging.warning("Retrying NBA request for %s", key)
                            time.sleep(5)
                    value = json.dumps(loaded, allow_nan=False)
                    updated, retry, stale = now, 0, False
                except Exception:
                    logging.exception('NBA request failed for %s', key)
                    retry = now + 300
                db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)', (key, value, updated, retry))
            return {'data': json.loads(value) if value is not None else None,
                    'updated': updated, 'stale': stale,
                    'error': 'NBA data is temporarily unavailable. Showing saved data where available.' if stale else None}

class NBA:
    def __init__(self, cache, season):
        self.cache, self.season = cache, season

    def standings(self, phase):
        def load():
            rows = records(leaguestandingsv3.LeagueStandingsV3(season=self.season, season_type=phase, timeout=30).standings)
            # Preseason responses can include international exhibition opponents.
            rows = [r for r in rows if r['TeamID'] in BY_ID]
            if len({r['TeamID'] for r in rows}) != 30:
                raise ValueError('Incomplete standings')
            return rows
        return self.cache.get(f'{self.season}:standings:{phase}', STANDINGS_TTL, load)

    def schedule(self):
        return self.cache.get(f'{self.season}:schedule', SCORES_TTL, lambda: records(
            scheduleleaguev2.ScheduleLeagueV2(season=self.season, timeout=30).season_games))

    def roster(self, team):
        return self.cache.get(f'{self.season}:roster:{team}', STANDINGS_TTL, lambda: records(
            commonteamroster.CommonTeamRoster(team_id=team, season=self.season, timeout=30).common_team_roster))

    def averages(self, team, phase):
        return self.cache.get(f'{self.season}:averages:{team}:{phase}', SCORES_TTL, lambda: records(
            leaguedashplayerstats.LeagueDashPlayerStats(team_id_nullable=team, season=self.season,
                season_type_all_star=phase, per_mode_detailed='PerGame', timeout=30).league_dash_player_stats))

    def game(self, game_id):
        def load():
            endpoint = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, timeout=30)
            return {'players': records(endpoint.player_stats), 'teams': records(endpoint.team_stats)}
        return self.cache.get(f'game:{game_id}', SCORES_TTL, load)
