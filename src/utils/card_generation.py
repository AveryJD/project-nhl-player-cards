# ====================================================================================================
# FUNCTIONS FOR GENERATING DIFFERENT SETS OF PLAYER CARDS
# ====================================================================================================

# Imports
from utils import card_functions as cf
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR


def make_player_card(player_name: str, season: str, pos: str) -> None:
    """
    Generate a player card for a specific player.

    :param player_name: a str of the player's full name ('First Last')
    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the player's position ('F', 'D', or 'G')
    :return: None
    """
    cf.make_player_card(player_name, season, pos)


def make_specific_player_cards(specific_players: list, cur_season: str, pos: str) -> None:
    """
    Generate player cards for a list of specific players.

    :param specific_players: a list of str player names ('First Last')
    :param cur_season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the players' position ('F', 'D', or 'G')
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
    for pos in ['F', 'D', 'G']:
        cur_season_data = file.load_card_data_csv(season, pos)
        for _, player_row in cur_season_data.iterrows():
            if player_row['Team'] == team:
                player_name = player_row['Player']
                cf.make_player_card(player_name, season, pos)


def make_position_player_cards(season: str, pos: str) -> None:
    """
    Generate player cards for all players of a given position during a specific season.

    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the position ('F', 'D', or 'G')
    :return: None
    """
    cur_season_data = file.load_card_data_csv(season, pos)
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, pos)


def make_all_player_cards(season: str) -> None:
    """
    Generate player cards for every player in all positions for a given season.

    :param season: a str representing the season ('YYYY-YYYY')
    :return: None
    """
    for pos in ['F', 'D', 'G']:
        cur_season_data = file.load_card_data_csv(season, pos)
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, pos)


def make_rank_player_cards(rank: str, season: str, pos: str) -> None:
    """
    Generate player cards for all players of a specific position, sorted by a given attribute rank.

    :param rank: a str of the attribute name to sort by (e.g. 'evo')
    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the position ('F', 'D', or 'G')
    :return: None
    """
    cur_season_data = file.load_card_data_csv(season, pos)
    cur_season_data = cur_season_data.sort_values(by=f'{rank}_rank', ascending=True)

    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, pos)
