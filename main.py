import base64
import logging
import jinja2
import math
import os
import random


from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp.util import run_wsgi_app


from lib import bottle
from lib.bottle import abort, post, get, request, error, debug, redirect, response

from models import BaseEntry


SIZE = 1000000
MAX_FLAGS_BEFORE_DELETION = 3

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'])


def user_key(user):
    return ndb.Key('User', user.user_id())


def get_random_base(town_hall_level=None):

    return random.choice(keys).get()


@get('/')
def display_base():

    return respond(JINJA_ENV.get_template('base_display.html'), template_values)


@post('/')
def vote_base():
    redirect('/')


@get('/upload')
def upload_base():
    logging.info("Ready to upload a base!")
    user = users.get_current_user()

    template_values = {
        'user': True,
        'url': '/upload'
    }

    # if there isn't a user re-direct to the login screen
    if not user:
        template_values['user'] = False

    if request.query.ni:
        template_values['no_image'] = True
    elif request.query.tl:
        template_values['too_large'] = True
    elif request.query.nl:
        template_values['no_level'] = True

    return respond(JINJA_ENV.get_template('upload.html'), template_values)


@post('/upload')
def create_base():
    logging.info("Creating a new base")

    # make sure all the information is included
    user = users.get_current_user()

    base_img = request.files.get('img')
    if base_img:
        logging.info('have an image!')
    else:
        redirect('/upload?ni=True')

    if request.forms.get('level'):
        logging.info('have a level')
    if request.forms.get('level') == 'Select':
        redirect('/upload?nl=True')

    if user:
        base_entry = BaseEntry(parent=user_key(user))
        base_entry.author = user
    else:
        base_entry = BaseEntry()

    base_entry.town_hall_level = int(request.forms.get('level'))

    # do the image processing
    base_entry.image = create_base_image(base_img, base_entry.town_hall_level)

    base_entry.random = random.randrange(0, math.pow(2, 52) - 1)
    base_entry.put()

    redirect('/display/{}'.format(base_entry.key.urlsafe()))


@get('/display/:base_id')
def display_one_base(base_id):
    base = ndb.Key(urlsafe=base_id).get()
    if not base:
        abort(404, 'base not found')

    user = users.get_current_user()
    template_values = {
        'user': True,
        'url': '/',
        'image': base64.b64encode(base.image),
        'score': int(base.score * 100)
    }
    if not user:
        template_values['user'] = False

    return respond(JINJA_ENV.get_template('display_one_base.html'), template_values)


@get('/logout')
def log_out():
    redirect(users.create_logout_url('/'))


@get('/login')
def log_in():
    redirect(users.create_login_url('/'))


def respond(template_file, params):
    tpl = JINJA_ENV.get_template(template_file)
    return tpl.render(**params)


def main():
    debug(False)
    app = bottle.app()
    run_wsgi_app(app)


@error(403)
def error_403(code):
    return "something weird has happened (403)"


@error(404)
def error_404(code):
    return "not found! (404)"


if __name__ == "__main__":
    main()
