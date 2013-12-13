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

from images import create_base_image
from models import BaseEntry


SIZE = 1000000
MAX_FLAGS_BEFORE_DELETION = 3

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'])


def user_key(user):
    return ndb.Key('User', user.user_id())


def get_random_base(town_hall_level=None):
    logging.info("choosing a random base")
    if town_hall_level:
        town_hall_level = int(town_hall_level)

    keys = []
    seed = random.randrange(0, math.pow(2, 52) - 1)

    # look for keys greater than
    logging.info("Looking at town hall level {} with "
                 "seed {}".format(town_hall_level, seed))
    query = BaseEntry.query()
    if town_hall_level:
        query.filter(BaseEntry.town_hall_level == town_hall_level)
    base_keys = query.filter(BaseEntry.random >= seed).fetch(10, keys_only=True)
    for base_key in base_keys:
        keys.append(base_key)
    # look for keys less than
    if not keys:
        query = BaseEntry.query()
        if town_hall_level:
            query.filter(BaseEntry.town_hall_level == town_hall_level)
        query.filter(BaseEntry.random < seed)
        base_keys = query.fetch(10, keys_only=True)
        for base_key in base_keys:
            keys.append(base_key)

    # if not keys, 404!
    if not keys:
        logging.info("Returning 404!!!")
        return abort(404, "No town halls found!")

    return random.choice(keys).get()


@get('/')
def display_base():
    logging.info("Displaying a base!")
    template_values = {}
    user = users.get_current_user()
    if request.query.base:
        # display the base
        logging.info("provided a base!")
        base = ndb.Key(urlsafe=request.query.base).get()
    else:
        # choose a random base
        logging.info("Choosing a random base")
        base = get_random_base(request.query.thl)

    if not base:
        logging.error("NO BASE")
        abort(404, "No town halls found!")

    if 'last' in request.query.keys():
        template_values['last'] = request.query.last

    template_values['base'] = base
    template_values['image'] = base64.b64encode(base.image)
    template_values['key'] = base.key.urlsafe()
    template_values['url'] = '/'
    if user:
        template_values['user'] = True

    return respond(JINJA_ENV.get_template('base_display.html'), template_values)


@post('/')
def vote_base():
    if 'key' in request.forms.keys():
        base = ndb.Key(urlsafe=request.forms.key).get()
        logging.info("we have a key")
        if 'clash' in request.forms.keys():
            logging.debug("Clashed!")
            base.clash += 1
            base.flags = 0
            base.put()
            pass
        elif 'next' in request.forms.keys():
            logging.debug("Nexted!")
            base.next += 1
            base.flags = 0
            base.put()
            pass
        elif 'flag' in request.forms.keys():
            logging.debug("Flagged!")
            base.flags += 1
            if base.flags >= MAX_FLAGS_BEFORE_DELETION:
                base.key.delete()
            else:
                base.put()
            redirect('/?last={}'.format('tyvm'))
        else:
            logging.error("Did have a next, clash, or flag!")
        logging.info(base.score)
        percentage = int(math.floor(base.score * 100))

        redirect('/?last={}'.format(percentage))
    else:
        logging.info("Diddn't find a key!")
        redirect('/')


@get('/base')
def my_bases():
    user = users.get_current_user()
    if not user:
        redirect(users.create_login_url(request.url))

    bases = BaseEntry.query(ancestor=user_key(user)).order(-BaseEntry.score).fetch(10)

    base_entries = []
    for base in bases:
        base_entries.append(
            (base64.b64encode(base.image), int(math.floor(base.score * 100)))
        )
    template_values = {
        'base_entries': base_entries,
        'url': '/base'
    }
    if user:
        template_values['user'] = True

    return respond(JINJA_ENV.get_template('my_bases.html'), template_values)


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


@get('/image/:img_id')
def get_image(img_id):
    base = ndb.Key(urlsafe=img_id).get()
    if base.image:
        logging.info("We have an image!")
        response.headers['Content-Type'] = 'image/png'
        response.body = base.image
        return response
    else:
        abort(404, 'image not found')


@error(403)
def error_403(code):
    return "something weird has happened (403)"


@error(404)
def error_404(code):
    return "not found! (404)"


if __name__ == "__main__":
    main()
