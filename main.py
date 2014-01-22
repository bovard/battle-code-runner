import logging
import math
import jinja2
import json
import os


from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import ndb


from lib import bottle
from lib.bottle import abort, post, get, request, error, debug, redirect, response

from models import Game, Team
from elo import calculate_new_elo


MAPS = ['backdoor.xml', 'bakedpotato.xml', 'blocky.xml', 'castles.xml', 'desolation.xml', 'divide.xml', 'donut.xml', 'flagsoftheworld.xml', 'flytrap.xml', 'friendly.xml', 'fuzzy.xml', 'itsatrap.xml', 'magnetism.xml', 'meander.xml', 'neighbors.xml', 'onramp.xml', 'overcast.xml', 'reticle.xml', 'rushlane.xml', 'siege.xml', 'smiles.xml', 'steamedbuns.xml', 'stitch.xml', 'sweetspot.xml', 'temple.xml', 'terra.xml', 'traffic.xml', 'troll.xml', 'valve.xml', 'ventilation.xml']


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


def _update_elo_with_teams(team_a, team_b, winner):
    team_a_elo = team_a.elo
    team_b_elo = team_b.elo
    team_a.elo = calculate_new_elo(team_a_elo, team_b_elo, winner == team_a.name)
    team_b.elo = calculate_new_elo(team_b_elo, team_a_elo, winner == team_b.name)


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

def _get_team_map_win_loss(team, map):
    team_a_count = Game.query().filter(Game.map == map).filter(Game.team_a == team.name).count()
    team_b_count = Game.query().filter(Game.map == map).filter(Game.team_b == team.name).count()
    win_count = Game.query().filter(Game.map == map).filter(Game.winner == team.name).count()
    game_count = team_b_count + team_a_count
    per = 0 if not game_count else round(100 * float(win_count)/game_count)
    return [map, game_count, win_count, per]



@get('/team/')
def display_team():
    sort_order = request.query.get('sort')
    team_name = request.query.get('team')
    team = Team.query().filter(Team.name == team_name).get()
    if not team:
        abort(404, 'team not found')

    data_list = []
    for map in MAPS:
        data_list.append(_get_team_map_win_loss(team, map))


    data_list = _sort_data_list(sort_order, data_list)

    template_values = {
        'headers': _add_sort_order_to_headers('/team/', ['Map', 'Games', 'Wins', 'Percentage'], {'team' :team_name}),
        'data_list': data_list
    }

    return respond(JINJA_ENV.get_template('data_view.html'), template_values)


@get('/delete_team/')
def delete_team():
    team_name = request.query.get('team')
    team = Team.query().filter(Team.name == team_name).get()
    to_delete = []
    if team:
        to_delete.append(team.key)

    gamesA = Game.query().filter(Game.team_a == team_name)
    for game in gamesA:
        to_delete.append(game.key)

    gamesB = Game.query().filter(Game.team_b == team_name)
    for game in gamesB:
        to_delete.append(game.key)

    logging.info('about to delete {} obj'.format(len(to_delete)))
    ndb.delete_multi(to_delete)


@get('/recompute/')
def recompute_elos():
    logging.info("fetching teams and making lookup")
    teams = Team.query().fetch(100)
    team_lookup = {}
    team_keys = []
    for team in teams:
        team_keys.append(team.key)
        team.elo = 1400
        team_lookup[team.name] = team

    logging.info('interating through games')
    games = Game.query()
    for game in games:
        _update_elo_with_teams(team_lookup[game.team_a], team_lookup[game.team_b], game.winner)

    logging.info('putting teams')
    ndb.put_multi(teams)
    logging.info('done')


def _get_team_name_link(name):
    return '<a href=/team/?team={}>{}</a>'.format(name, name)


def _get_team_win_loss(team):
    team_a_count = Game.query().filter(Game.team_a == team.name).count()
    team_b_count = Game.query().filter(Game.team_b == team.name).count()
    game_count = team_b_count + team_a_count
    win_count = Game.query().filter(Game.winner == team.name).count()
    per = round(100 * float(win_count)/game_count)
    return [_get_team_name_link(team.name), team.elo, game_count, win_count, per]


def _add_sort_order_to_headers(url, headers, qsp={}):
    for i in range(len(headers)):
        qsp_str = ''
        for key in qsp.keys():
            qsp_str = '{}&{}={}'.format(qsp_str, key, qsp.get(key))
        headers[i] = '<a href={}?sort={}{}>{}</a>'.format(url, i, qsp_str, headers[i])
    return headers


def _sort_data_list(sort_order, data_list):
    if sort_order is None:
        return data_list
    sort_order = int(sort_order)
    if sort_order == 0:
        return data_list

    data_list.sort(key=lambda data: data[sort_order])
    data_list.reverse()
    return data_list


@get('/teams/')
def display_teams():
    sort_order = request.query.get('sort')

    teams = Team.query().order(-Team.elo, Team.name).fetch(100)
    data_list = []
    for team in teams:
        data_list.append(_get_team_win_loss(team))

    data_list = _sort_data_list(sort_order, data_list)

    template_values = {
        'headers': _add_sort_order_to_headers('/teams/', ['Team', 'ELO', 'Games', 'Wins', 'Percentage']),
        'data_list': data_list
    }
    return respond(JINJA_ENV.get_template('data_view.html'), template_values)


@get('/')
def display_teams():
    sort_order = request.query.get('sort')

    teams = Team.query().order(-Team.elo, Team.name).fetch(100)

    data_list = []
    for team in teams:
        data_list.append([_get_team_name_link(team.name), team.elo])

    data_list = _sort_data_list(sort_order, data_list)

    template_values = {
        'headers': _add_sort_order_to_headers('/', ['Team', 'ELO']),
        'data_list': data_list
    }


    return respond(JINJA_ENV.get_template('data_view.html'), template_values)


def respond(template_file, params):
    tpl = JINJA_ENV.get_template(template_file)
    return tpl.render(**params)


def main():
    debug(True)
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
