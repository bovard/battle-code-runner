import math


def calculate_new_elo(elo, opponent_elo, win):
    expected = _calc_expected(elo, opponent_elo)
    new_elo = _updated_elo(elo, expected, win)

    # enforce minimum elo
    if new_elo < 100:
        new_elo = 100
    return new_elo


def _calc_expected(elo, opponent_elo):
    return 1.0/(1.0 + math.pow(10.0, (opponent_elo - elo)/400.0))


def _updated_elo(elo, expected, win):
    won = 0
    if win:
        won = 1
    return int(round(elo + 32 * (won - expected)))

