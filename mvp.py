"""MVP Ladder and opponent splits from completed regular-season box scores."""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from data import BY_ID, TEAMS, require

MVP_TTL = 12 * 60 * 60
STATS = {
    'MP': 'minutes', 'FG': 'fieldGoalsMade', 'FGA': 'fieldGoalsAttempted',
    '3P': 'threePointersMade', '3PA': 'threePointersAttempted',
    'FT': 'freeThrowsMade', 'FTA': 'freeThrowsAttempted',
    'STL': 'steals', 'BLK': 'blocks', 'TOV': 'turnovers',
    'TRB': 'reboundsTotal', 'AST': 'assists', 'PTS': 'points',
}
PERCENTAGES = {'FG%': ('FG', 'FGA'), '3P%': ('3P', '3PA'), 'FT%': ('FT', 'FTA')}
COLUMNS = 'G MP FG FGA FG% 3P 3PA 3P% FT FTA FT% STL BLK TOV TRB AST PTS'.split()
LADDER_COLUMNS = ['Player', 'Team', *COLUMNS, 'AVG']
PLAYER_COLUMNS = ['Opp', *COLUMNS, 'MVP']
WEIGHTS = {'PTS': 1, 'BLK': 4, 'STL': 4, 'AST': 2, 'TRB': 1, 'TOV': -2,
           'FG': 2, 'FGA': -1, 'FT': 1, 'FTA': -1, '3P': 1}


EASTERN_TEAMS = frozenset('ATL BOS BKN CHA CHI CLE DET IND MIA MIL NYK ORL PHI TOR WAS'.split())
TEAM_ALIASES = {'BRK': 'BKN', 'CHO': 'CHA', 'PHO': 'PHX'}


def mvp_team(abbr):
    code = TEAM_ALIASES.get(abbr, abbr)
    team = TEAMS.get(code)
    if team is None:
        return {'name': abbr, 'conference': ''}
    return {'name': team['full_name'], 'conference': 'East' if code in EASTERN_TEAMS else 'West'}


def abbreviated_player(name, position):
    first, separator, last = name.partition(' ')
    if separator and not first.endswith('.'):
        name = f'{first[0]}. {last}'
    return f'{name} - {position}' if position else name


def eligible(row):
    return not (row['G'] < 8 and row['MP'] < 12)


def normalize(name):
    ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_name.lower())


def seed_rows(season):
    if season != '2026-27':
        return []
    with Path(__file__).with_name('NBA_MVP3.csv').open(encoding='utf-8-sig', newline='') as file:
        rows = []
        for index, row in enumerate(csv.DictReader(file), 1):
            name, position = row['Player'].rsplit(' - ', 1)
            rows.append(dict(row, **{key: float(row[key]) for key in [*COLUMNS, 'AVG']},
                             name=name, position=position, id=f'seed-{index}', splits=[]))
        return rows


def summarize(lines):
    games = len(lines)
    totals = {key: sum(line[key] for line in lines) for key in STATS}
    return {
        'G': games,
        **{key: value / games for key, value in totals.items()},
        **{key: totals[made] / totals[attempted] if totals[attempted] else None
           for key, (made, attempted) in PERCENTAGES.items()},
        'MVP': sum(totals[key] * weight for key, weight in WEIGHTS.items()) / games,
    }


def build_ladder(source):
    seed = seed_rows(source.season)
    positions = {(normalize(row['name']), row['Team']): row['position'] for row in seed}
    players = {}
    for game in require(source.schedule()):
        if game['gameStatus'] != 3 or game['seasonType'] != 2:
            continue
        home, away = game['homeTeam_teamId'], game['awayTeam_teamId']
        box = require(source.game(game['gameId']))
        played = [line for line in box['players'] if line['played']]
        if {line['teamId'] for line in played} != {home, away}:
            raise ValueError('Missing played-player box scores')
        for line in played:
            name = line['firstName']
            team = BY_ID[line['teamId']]['abbreviation']
            opponent = BY_ID[away if line['teamId'] == home else home]['abbreviation']
            player = players.setdefault(line['personId'], {'splits': defaultdict(list)})
            short_name = name[0] + '. ' + name.split(' ', 1)[-1]
            position = positions.get((normalize(short_name), team)) or line.get('rosterPosition')
            player.update(name=name, Team=team, position=position or player.get('position', ''))
            stats = {key: line[field] for key, field in STATS.items()}
            if any(value is None for value in stats.values()):
                raise ValueError('Incomplete played-player box score')
            player['splits'][opponent].append(stats)

    rows = []
    for person_id, player in players.items():
        splits = player['splits']
        summary = summarize([line for lines in splits.values() for line in lines])
        position = player['position']
        rows.append(dict(summary, id=str(person_id), name=player['name'], Team=player['Team'],
                         position=position, Player=f"{player['name']} - {position}" if position else player['name'],
                         AVG=summary['MVP'],
                         splits=[dict(summarize(lines), Opp=opp) for opp, lines in sorted(splits.items())]))
    return sorted(rows, key=lambda row: (-row['AVG'], row['name']))
