from collections import namedtuple
from itertools import chain, groupby
import csv
import numpy
import os
import pandas as pd

class Tournament(object):

    Match = namedtuple("Match", ['gameId', 'date', 'time', 'team1', 'team2', 'group'])
    Prediction = namedtuple("Prediction", ['team1', 'team2', 'outcome', 'sd'])
    Team = namedtuple("Team", ['name', 'draw'])
    Result = namedtuple("Result", ['match', 'team1Score', 'team2Score'])
    TeamResult = namedtuple("TeamResult", ['name', 'opponent', 'group', 'gs', 'ga'])
    TeamRecord = namedtuple("TeamRecord", ['name', 'group', 'p', 'gs', 'ga', 'defeated'])

    def __init__(self):
        #self.schedule = self.loadCsv('data/wc2018schedule.csv', self.Match)
        self.schedule = self.loadCsv(os.path.join(os.getcwd(), 'tournament', 'data', 'schedule_fifa_fs.csv'), self.Match)
        self.predictions = self.loadCsv(os.path.join(os.getcwd(), 'tournament', 'data', 'wc2018staticPredictions.csv'), self.Prediction)
        self.teams = self.loadCsv(os.path.join(os.getcwd(), 'tournament', 'data', 'wc2018qualified.csv'), self.Team)


    def loadCsv(self, filepath, itemtype):
        with open(filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            return list(map(lambda row: itemtype(**row), reader))


    def getActualGroupMatch(self, match, teams):
        return self.Match(gameId = match.gameId, date = match.date, time = match.time, group = match.group,
            team1 = next(team.name for team in teams if team.draw == match.team1),
            team2 = next(team.name for team in teams if team.draw == match.team2),       
            )


    def getActualEliminationMatch(self, match, qualified):
        return self.Match(gameId = match.gameId, date = match.date, time = match.time, group = match.group,
            team1 = qualified[match.team1],
            team2 = qualified[match.team2],
            )


    def getResult(self, match, predictions):
        allowtie = match.group != None 
        prediction = next(pred for pred in predictions \
            if (pred.team1 == match.team1 and pred.team2 == match.team2) or \
                (pred.team1 == match.team2 and pred.team2 == match.team1)) 
        reverse = prediction.team1 != match.team1
        goaldiff = numpy.random.normal(float(prediction.outcome), float(prediction.sd))
        reverse = reverse != (goaldiff < 0) 
        normgoaldiff = 0 if abs(goaldiff) <= 0.4475 \
            else 1 if abs(goaldiff) < 1 else round(abs(goaldiff))
        if not(allowtie) and normgoaldiff == 0:
            normgoaldiff = 1
        losergoals = round(abs(numpy.random.normal(0, 1)))
        return self.Result(match, losergoals, losergoals + normgoaldiff) if reverse \
            else self.Result(match, losergoals + normgoaldiff, losergoals)


    def getTeamPerfFromResult(self, result):
        return [self.TeamResult(name=result.match.team1, opponent=result.match.team2, group=result.match.group, gs=result.team1Score, ga=result.team2Score),
        self.TeamResult(name=result.match.team2, opponent=result.match.team1, group=result.match.group, gs=result.team2Score, ga=result.team1Score)]


    def getTeamRecord(self, name, teamResults):
        points = w = d = gs = ga = 0
        group = ''
        defeated = []
        for result in teamResults:
            group = result.group
            gs += result.gs
            ga += result.ga
            if result.gs > result.ga:
                w += 1
                defeated.append(result.opponent)
            elif result.gs == result.ga:
                d += 1
        return self.TeamRecord(name=name, group=group, p=3*w+d, gs=gs, ga=ga, defeated=defeated)


    def runGroupStage(self, schedule, predictions, teams):
        groupschedule = list(map(lambda x: self.getActualGroupMatch(x, teams), filter(lambda x: x.group != None, schedule)))
        groupresults = list(map(lambda x: self.getResult(x, predictions), groupschedule))
        groupperfs = list(chain.from_iterable(map(self.getTeamPerfFromResult, groupresults)))
        records = []
        for k, g in groupby(sorted(groupperfs, key=lambda x: x.name), key=lambda x: x.name):
            records.append(self.getTeamRecord(k, g))

        qualified = {}
        group_standings = {}
        group_table_total = {}
        for k, g in groupby(sorted(records, key=lambda x: x.group), key=lambda x: x.group):
            grouptable = sorted(g, key=lambda x: 1000000*x.p + 10000*(x.gs-x.ga) + 100*(x.gs), reverse=True)
            qualified['1' + k] = grouptable[0].name
            qualified['2' + k] = grouptable[1].name
            
            group_standings['1' + k] = grouptable[0].name
            group_standings['2' + k] = grouptable[1].name
            group_standings['3' + k] = grouptable[2].name
            group_standings['4' + k] = grouptable[3].name
            
            
            
            group_table_standings = []
            
            group_table_standings.append([grouptable[0].name, grouptable[0].gs, grouptable[0].ga, grouptable[0].p])
            group_table_standings.append([grouptable[1].name, grouptable[1].gs, grouptable[1].ga, grouptable[1].p])
            group_table_standings.append([grouptable[2].name, grouptable[2].gs, grouptable[2].ga, grouptable[2].p])
            group_table_standings.append([grouptable[3].name, grouptable[3].gs, grouptable[3].ga, grouptable[3].p])
            
            group_table_total[grouptable[0].group] = group_table_standings
        return qualified, group_standings, groupresults, group_table_total


    def runEliminationRound(self, round, prevround, schedule, predictions):
        roundschedule = list(map(lambda x: self.getActualEliminationMatch(x, prevround), filter(lambda x: x.gameId.startswith('G'+round), schedule)))
        roundresults = list(map(lambda x: self.getResult(x, predictions), roundschedule))
        results = {}
        for result in roundresults:
            results['W' + result.match.gameId] = result.match.team1 if result.team1Score > result.team2Score \
                else result.match.team2
            results['L' + result.match.gameId] = result.match.team1 if result.team1Score < result.team2Score \
                else result.match.team2
        return results, roundresults


    def get_tournament_prediction(self):
        results, group_standings, groupresults, group_table_total = self.runGroupStage(self.schedule, self.predictions, self.teams)
        group_winners = results
        all_rounds = []
        for rnd in ['AF','QF','SF','FN']:
            results, roundresults = self.runEliminationRound(rnd, results, self.schedule, self.predictions)
            all_rounds.append(roundresults)


        columns = ['gameID', 'date', 'team1', 'team2', 'group', 'result']
        new_df = pd.DataFrame(columns=columns)
        for match in groupresults:
            new_df = new_df.append(pd.DataFrame([[match.match.gameId,
                                                match.match.date, 
                                                match.match.team1, 
                                                match.match.team2, 
                                                match.match.group, 
                                                '{}-{}'.format(int(match.team1Score),
                                                                int(match.team2Score))]],
                                                columns=columns))
            

        for round in all_rounds:
            for match in round:
                new_df = new_df.append(pd.DataFrame([[match.match.gameId,
                                                    match.match.date, 
                                                    match.match.team1, 
                                                    match.match.team2, 
                                                    match.match.group, 
                                                    '{}-{}'.format(int(match.team1Score),
                                                                    int(match.team2Score))]],
                                                    columns=columns))

        return group_winners, new_df, group_table_total
