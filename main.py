import jinja2
import os
import webapp2
import datetime

from google.appengine.ext import ndb

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Error(Exception):
  """Generic error class."""

class RapidVoterError(Error):
  """Raised when someone votes too quickly."""
  
class Vote(ndb.Model):
  source_ip = ndb.StringProperty()  # source IP
  timestamp = ndb.DateTimeProperty(auto_now_add=True)
  
class Dodger(ndb.Model):
  """The ID should be the username."""
  votes = ndb.StructuredProperty(Vote, repeated=True)
  count = ndb.ComputedProperty(lambda self: len(self.votes))

  @classmethod
  def Increment(cls, dodger_name, source_ip):
    limit = datetime.datetime.now() - datetime.timedelta(days=1)
    dodger_name = dodger_name.lower()
    dodger = cls.get_by_id(dodger_name) or cls(id=dodger_name)
    for vote in dodger.votes:
      if vote.source_ip == source_ip and vote.timestamp > limit:
        raise RapidVoterError('You must wait: %s' % (vote.timestamp-limit))
    dodger.votes.append(Vote(source_ip=source_ip))
    dodger.put()
    return dodger.count


class DDHandler(webapp2.RequestHandler):
  def RenderTemplate(self, filename, vars):
    template = jinja_environment.get_template(filename)
    self.response.out.write(template.render(vars))

class MainPageHandler(DDHandler):
  def get(self):
    self.RenderTemplate('templates/base.html', {'got_it': 'a dog!'})

class IncrementHandler(DDHandler):
  def get(self):
    dodger_name = self.request.get('username')
    try:
      count = Dodger.Increment(dodger_name, self.request.remote_addr)
      self.response.out.write(count)
    except RapidVoterError as err:
      self.response.out.write(err)

class DirtyDodgersHandler(DDHandler):
  def get(self):
    results = Dodger.query().order(-Dodger.count).fetch(limit=10)
    for dodger in results:
      self.response.out.write(str(dodger.count) + ' ' + dodger.key.id() + '<br>')
    

app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/add', IncrementHandler),
                               ('/dodgers', DirtyDodgersHandler)],
                              debug=True)
