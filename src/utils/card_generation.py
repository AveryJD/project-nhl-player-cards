# ====================================================================================================
# FUNCTIONS FOR GENERATING DIFFERENT SETS OF PLAYER CARDS
# ====================================================================================================

# Imports
from utils import card_functions as cf
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR


def make_player_card(player_name: str, season: str, pos: str, mode: str = 'light') -> None:
    """
    Generate a player card for a specific player.

    :param player_name: A str of the player's full name ('First Last')
    :param season: A str representing the season ('YYYY-YYYY')
    :param pos: A str representing the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """
    cf.make_player_card(player_name, season, pos, mode=mode)


def make_team_player_cards(team: str, season: str, mode: str = 'light') -> None:
    """
    Generate player cards for every player on a specific team during a given season.

    :param team: A str representing the team abbreviation (e.g. 'TOR')
    :param season: A str representing the season ('YYYY-YYYY')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """
    for pos in ['F', 'D', 'G']:
        cur_season_data = file.load_card_data_csv(season, pos)
        for _, player_row in cur_season_data.iterrows():
            if player_row['Team'] == team:
                player_name = player_row['Player']
                cf.make_player_card(player_name, season, pos, mode=mode)


def make_all_position_player_cards(season: str, pos: str, mode: str = 'light') -> None:
    """
    Generate player cards for all players of a given position during a specific season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param pos: A str representing the position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """
    cur_season_data = file.load_card_data_csv(season, pos)
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, pos, mode=mode)


def make_all_player_cards(season: str, mode: str = 'light') -> None:
    """
    Generate player cards for every player in all positions for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """
    for pos in ['F', 'D', 'G']:
        cur_season_data = file.load_card_data_csv(season, pos)
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, pos, mode=mode)


