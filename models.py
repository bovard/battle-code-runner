from google.appengine.ext import ndb


class Submission(ndb.Model):
    author = ndb.UserProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    games_played = ndb.IntegerProperty(default=0)
    ranking = ndb.IntegerProperty(default=1400)
    active = ndb.BooleanProperty(default=True)
    files = ndb.BlobProperty()


class Game(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)
    home_player = ndb.UserProperty()
    away_player = ndb.UserProperty()
    winner = ndb.UserProperty()
    game_file = ndb.BlobProperty()