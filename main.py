import base64
import datetime
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

from models import Game, Team
from elo import calculate_new_elo



JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'])

def _get_game(team_a, team_b, map):
    games = Game.query().filter(Game.team_a, team_a).filter(Game.team_b, team_b).filter(Game.map, map).fetch(10)
    if not games.length:
        return None

    if games.length == 1:
        return games[0]

    if games.length > 1:
        logging.error("Found more than 1 game for {} vs {} on {}".format(team_a, team_b, map))
        return games[0]

def _create_or_get_team(team_name):
    team = Team.query(Team.name, team_name).get()
    if not team:
        team = Team(name = team_name)
    return team


def _create_and_save_game(team_a, team_b, map, winner, round):
    team_a_team = _create_or_get_team(team_a)
    team_b_team = _create_or_get_team(team_b)
    team_a_elo = team_a_team.elo
    team_b_elo = team_b_team.elo
    team_a_team.elo = calculate_new_elo(team_a_elo, team_b_elo, winner == team_a)
    team_b_team.elo = calculate_new_elo(team_b_elo, team_a_elo, winner == team_b)
    game = Game(
        team_a=team_a,
        team_b=team_b,
        winner=winner,
        round=round,
        map=map
    )
    ndb.put_multi([game, team_a_team, team_a_team])


@get('/game/')
def display_game():
    team_a = request.query.team_a
    team_b = request.query.team_b
    map = request.query.map

    game = _get_game(team_a, team_b, map)

    if game:
        response.headers['Content-Type'] = 'application/json'
        response.body = game.to_json()
        return response
    else:
        abort(404, 'game not found')

@post('/game/')
def save_game():
    team_a = request.query.get(Game.TEAM_A)
    team_b = request.query.get(Game.TEAM_B)
    map = request.query.get(Game.MAP)
    winner = request.query.get(Game.WINNER)
    round = request.query.get(Game.ROUND)
    game = _get_game(team_a, team_b, map)
    if not game:
        _create_and_save_game(team_a, team_b, map, winner, round)


@get('/')
def display_teams():

    teams = Team.query().order(Team.elo, Team.name).fetch(100)

    template_values = {
        teams: teams
    }

    return respond(JINJA_ENV.get_template('display_teams.html'), template_values)


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
