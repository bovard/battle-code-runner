from google.appengine.ext import ndb


class BaseEntry(ndb.Model):
    author = ndb.UserProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    image = ndb.BlobProperty(indexed=False)
    blob_key = ndb.BlobKeyProperty()
    clash = ndb.IntegerProperty(default=0)
    next = ndb.IntegerProperty(default=0)
    score = ndb.ComputedProperty(
        lambda self: float(self.next + 1)/(self.next + self.clash + 2))
    town_hall_level = ndb.IntegerProperty(default=1)
    random = ndb.IntegerProperty()
    flags = ndb.IntegerProperty(default=0)


class Submission(ndb.Model):
    author = ndb.UserProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    games_played = ndb.IntegerProperty(default=0)
    ranking = ndb.IntegerProperty(default=1400)
