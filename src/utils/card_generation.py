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
    Make a specific player card.
    """

    cf.make_player_card(player_name, season, pos, custom_team)




def make_specific_player_cards(specific_players: list, cur_season: str, pos: str) -> None:
    """
    Make a player card for every player in a list of specific players.
    """

    for player_name in specific_players:
        cf.make_player_card(player_name, cur_season, pos)




def make_team_player_cards(team: str, season: str) -> None:
    """
    Make a player card for every player on a specific team.
    """
    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'f')

    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'd')

    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        if player_row['Team'] == team:
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'g')



def make_position_player_cards(season: str, pos: str) -> None:
    """
    Make a player card for every player that plays a specific position.
    """
    if pos == 'f':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'f')

    elif pos == 'd':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'd')

    elif pos == 'g':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'g')



def make_all_player_cards(season: str) -> None:
    """
    Make a player card for every player that has played in a specific season.
    """
    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'f')

    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_data/defense_rankings/{season}_d_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'd')

    cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_rankings/{season}_g_rankings.csv')
    for _, player_row in cur_season_data.iterrows():
        player_name = player_row['Player']
        cf.make_player_card(player_name, season, 'g')



def make_rank_player_cards(rank: str, season: str, pos: str) -> None:
    """
    Make a player card for every player that has played in a specific season, ordered by a specified attribute rank.
    """
    if pos == 'f':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv')
        cur_season_data = cur_season_data.sort_values(by=f'{rank}_rank', ascending=True)
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'f')

    elif pos == 'd':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv')
        cur_season_data = cur_season_data.sort_values(by=f'{rank}_rank', ascending=True)
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'd')

    elif pos == 'g':
        cur_season_data =  pd.read_csv(f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv')
        cur_season_data = cur_season_data.sort_values(by=f'{rank}_rank', ascending=True)
        for _, player_row in cur_season_data.iterrows():
            player_name = player_row['Player']
            cf.make_player_card(player_name, season, 'g')

