from google.appengine.ext import ndb


class Game(ndb.Model):
    TEAM_A = 'teamA'
    TEAM_B = 'teamB'
    WINNER = 'winner'
    ROUND = 'round'
    MAP = 'map'


    date = ndb.DateTimeProperty(auto_now_add=True)
    map = ndb.StringProperty()
    team_a = ndb.StringProperty()
    team_b = ndb.StringProperty()
    winner = ndb.StringProperty()
    round = ndb.IntegerProperty()

    def to_json(self):
        return {
            self.MAP: self.map,
            self.TEAM_A: self.team_a,
            self.TEAM_B: self.team_b,
            self.WINNER: self.winner,
            self.ROUND: self.round
        }


class Team(ndb.Model):
    name = ndb.StringProperty()
    elo = ndb.IntegerProperty(default=1400)
