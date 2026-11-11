import tempfile
import unittest
from unittest.mock import Mock
from data import NBA, Cache, TEAMS, BY_ESPN


class ESPNAdapterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.nba = NBA(Cache(self.directory.name+'/data.sqlite3'), '2026-27')

    def test_saved_pick_team_identifiers_remain_compatible(self):
        self.assertEqual(TEAMS['DET']['id'], 1610612765)
        self.assertEqual(BY_ESPN['8']['id'], TEAMS['DET']['id'])

    def test_box_score_starters_dnp_and_shooting_percentages(self):
        team = {'id': '8'}
        def athlete(pid, starter, dnp, stats):
            return {'athlete': {'id':str(pid), 'displayName':'Test Player','position':{'abbreviation':'G'}},
                    'starter':starter, 'didNotPlay':dnp,'stats':stats}
        payload = {'header':{'competitions':[{'status':{'type':{'completed':True}},
                   'competitors':[{'id':'8','score':'100'},{'id':'2','score':'90'}]}]},
                   'boxscore':{'players':[
                       {'team':team,'statistics':[{'labels':['MIN','PTS','FG','3PT','FT','REB','AST','TO','STL','BLK'],
                        'athletes':[athlete(1,True,False,['30:30','12','4-10','1-3','3-4','4','5','2','1','0']),
                                    athlete(2,False,True,[]),
                                    athlete(3,False,False,['--','0','0-0','0-0','0-0','0','0','0','0','0'])]}]},
                       {'team':{'id':'2'},'statistics':[]}]}}
        self.nba.fetch = Mock(return_value=payload)
        result = self.nba.game('401000001')
        self.assertIsNone(result['error'])
        player, dnp, zero = result['data']['players']
        self.assertFalse(zero['played'])
        self.assertEqual(player['position'],'G')
        self.assertEqual(player['minutes'],30.5)
        self.assertEqual(player['fieldGoalsPercentage'],.4)
        self.assertFalse(dnp['played'])
        self.assertIsNone(dnp['points'])

    def test_averages_exclude_dnp_and_weight_shooting_by_attempts(self):
        tid = TEAMS['DET']['id']
        def response(data): return {'data':data,'error':None,'updated':1}
        self.nba.schedule = Mock(return_value=response([
            {'gameId':str(i),'gameStatus':3,'homeTeam_teamId':tid,'awayTeam_teamId':0} for i in range(2)]))
        def player(made, attempts, played=True):
            return dict(personId=1, teamId=tid, played=played, minutes=30,points=10,assists=2,reboundsTotal=4,
                steals=1,blocks=0,turnovers=1,fieldGoalsMade=made,fieldGoalsAttempted=attempts,
                threePointersMade=0,threePointersAttempted=0,freeThrowsMade=2,freeThrowsAttempted=2)
        self.nba.game = Mock(side_effect=[response({'players':[player(1,2),dict(player(0,0,False),personId=2)]}),
                                         response({'players':[player(3,10)]})])
        result=self.nba.averages(tid,'Regular Season')
        self.assertIsNone(result['error'])
        self.assertEqual(len(result['data']),1)
        row=result['data'][0]
        self.assertEqual(row['GP'],2)
        self.assertEqual(row['FG_PCT'],4/12)
        self.assertEqual(row['PTS'],10)
        self.assertIsNone(row['FG3_PCT'])

    def test_missing_completed_box_prevents_publication(self):
        self.nba.fetch = Mock(return_value={'header':{'competitions':[{'status':{'type':{'completed':True}}}]},'boxscore':{}})
        with self.assertLogs(level='ERROR'):
            result=self.nba.game('401000002')
        self.assertIsNone(result['data'])
        self.assertIsNotNone(result['error'])


if __name__ == '__main__': unittest.main()
