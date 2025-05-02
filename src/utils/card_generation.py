# ====================================================================================================
# FUNCTIONS FOR GENERATING DIFFERENT SETS OF PLAYER CARDS
# ====================================================================================================

# Imports
import pandas as pd
from utils import card_functions as cf
from utils import constants

DATA_DIR = constants.DATA_DIR


def make_player_card(player_name: str, season: str, pos: str, custom_team='NONE') -> None:
    """
    Generate a player card for a specific player.

    :param player_name: a str of the player's full name ('First Last')
    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the player's position ('f', 'd', or 'g')
    :param custom_team: an optional str for changing the player's team on the card
    :return: None
    """
    cf.make_player_card(player_name, season, pos, custom_team)


def make_specific_player_cards(specific_players: list, cur_season: str, pos: str) -> None:
    """
    Generate player cards for a list of specific players.

    :param specific_players: a list of str player names ('First Last')
    :param cur_season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the players' position ('f', 'd', or 'g')
    :return: None
    """
    for player_name in specific_players:
        cf.make_player_card(player_name, cur_season, pos)


def make_team_player_cards(team: str, season: str) -> None:
    """
    Generate player cards for every player on a specific team during a given season.

    :param team: a str representing the team abbreviation (e.g. 'TOR')
    :param season: a str representing the season ('YYYY-YYYY')
    :return: None
    """
    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'f')

    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'd')

    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'g')


def make_position_player_cards(season: str, pos: str) -> None:
    """
    Generate player cards for all players of a given position during a specific season.

    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the position ('f', 'd', or 'g')
    :return: None
    """
    if pos == 'f':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    elif pos == 'd':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
    elif pos == 'g':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
    else:
        return

    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, pos)


def make_all_player_cards(season: str) -> None:
    """
    Generate player cards for every player in all positions for a given season.

    :param season: a str representing the season ('YYYY-YYYY')
    :return: None
    """
    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'f')

    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'd')

    cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'g')


def make_rank_player_cards(rank: str, season: str, pos: str) -> None:
    """
    Generate player cards for all players of a specific position, sorted by a given attribute rank.

    :param rank: a str of the attribute name to sort by (e.g. 'off')
    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the position ('f', 'd', or 'g')
    :return: None
    """
    if pos == 'f':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    elif pos == 'd':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
    elif pos == 'g':
        cur_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
    else:
        return

    cur_season_data = cur_season_data.sort_values(by=f'{rank}_rank', ascending=True)
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, pos)
