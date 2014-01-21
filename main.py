import logging
import math
import jinja2
import json
import os


from google.appengine.ext.webapp.util import run_wsgi_app


from lib import bottle
from lib.bottle import abort, post, get, request, error, debug, redirect, response

from models import Game, Team
from elo import calculate_new_elo



JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates'),
    extensions=['jinja2.ext.autoescape'])

def _get_game(team_a, team_b, map):
    logging.info('get_game: {}, {}, {}'.format(team_a, team_b, map))
    games = Game.query().filter(Game.team_a == team_a).filter(Game.team_b == team_b).filter(Game.map == map).fetch(10)
    if not len(games):
        return None

    if len(games) == 1:
        return games[0]

    if len(games) > 1:
        logging.error("Found more than 1 game for {} vs {} on {}".format(team_a, team_b, map))
        return games[0]

def _create_or_get_team(team_name):
    logging.info('create_or_get_team: {}'.format(team_name))
    team = Team.query().filter(Team.name == team_name).get()
    if not team:
        team = Team(name = team_name)
    logging.info('returning {}'.format(team))
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
    logging.info('about to put {}, {} and {}'.format(game, team_a_team, team_b_team))
    game.put()
    team_a_team.put()
    team_b_team.put()


@get('/game/')
def display_game():
    team_a = request.query.get(Game.TEAM_A)
    team_b = request.query.get(Game.TEAM_B)
    map = request.query.get(Game.MAP)

    game = None
    if team_a and team_b and map:
        game = _get_game(team_a, team_b, map)

    if game:
        response.headers['Content-Type'] = 'application/json'
        logging.info(game.to_json())
        response.body = json.dumps(game.to_json())
        return response
    else:
        abort(404, 'game not found')

@post('/game/')
def save_game():
    team_a = request.query.get(Game.TEAM_A)
    team_b = request.query.get(Game.TEAM_B)
    map = request.query.get(Game.MAP)
    winner = request.query.get(Game.WINNER)
    round = int(request.query.get(Game.ROUND))
    logging.info('{},{},{},{},{}'.format(team_a, team_b, map, winner, round))
    game = _get_game(team_a, team_b, map)
    if not game:
        _create_and_save_game(team_a, team_b, map, winner, round)

@get('/team/')
def display_team():
    team_name = request.query.get('team')
    team = Team.query().filter(Team.name == team_name).get()
    if not team:
        abort(404, 'team not found')

    team_a_count = Game.query().filter(Game.team_a == team_name).count()
    team_b_count = Game.query().filter(Game.team_b == team_name).count()
    game_count = team_b_count + team_a_count
    win_count = Game.query().filter(Game.winner == team_name).count()
    per = round(100 * float(win_count)/game_count)

    template_values = {
        'team': team,
        'games': game_count,
        'wins': win_count,
        'percentage': per
    }

    return respond(JINJA_ENV.get_template('display_one_team.html'), template_values)


@get('/')
def display_teams():

    teams = Team.query().order(-Team.elo, Team.name).fetch(100)

    template_values = {
        'teams': teams
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
