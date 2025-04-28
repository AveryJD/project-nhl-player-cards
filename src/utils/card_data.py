# ====================================================================================================
# FUNCTIONS FOR GETTING DATA TO BE USED IN PLAYER CARDS
# ====================================================================================================

import sys
DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'
sys.path.append(f'{DATA_DIR}')

# Imports
import pandas as pd


def get_player_role(player_row: pd.Series) -> str:
    """
    Get an str for a player's time on ice allocation.

    :param player_row: a Series containing player data
    :return: a str of the toi allocation
    """
    
    if player_row['Position'] == 'G':
        games_played = player_row['GP']
        if games_played >= 50:
            role = 'Starter'
        elif games_played > 41:
            role = '1A'
        elif games_played > 32:
            role = '1B'
        elif games_played > 8:
            role = 'Backup'
        else:
            role = 'Fringe'

    elif player_row['Position'] == 'D':
        avg_toi = player_row['TOI'] / player_row['GP']
        if avg_toi >= 22.0:
            role = 'First Pair'
        elif avg_toi > 18.0:
            role = 'Second Pair'
        elif avg_toi > 13.0:
            role = 'Third Pair'
        else:
            role = 'Fringe'

    else:
        avg_toi = player_row['TOI'] / player_row['GP']
        if avg_toi >= 18.0:
            role = 'First Line'
        elif avg_toi > 15.5:
            role = 'Second Line'
        elif avg_toi > 8.5:
            role = 'Bottom 6'
        else:
            role = 'Fringe'

    return role


def get_rank_and_percentile(player_row: pd.Series, attribute_rank_name: str, total_players: int) -> tuple[int, int]:
    """
    Get the player's rank and percentile of a given attribute.

    :param player_row: a series from a data frame containing player ranks
    :param attribute_rank_name: a str of the attribute name of the rank to get
    :param total_players: an int of the total players that qualify for the attribute
    :return: a tuple of the player's rank and percentile for the given attribute
    """
    if attribute_rank_name == "ppl_rank" and player_row['ppl_score'] == -999999:
        rank = 'N/A'
        percentile = 100
    elif attribute_rank_name == "pkl_rank" and player_row['pkl_score'] == -999999:
        rank = 'N/A'
        percentile = 100
    elif attribute_rank_name == "fof_rank" and player_row['fof_score'] == -999999:
        rank = 'N/A'
        percentile = 100
    else:
        rank = int(player_row[attribute_rank_name])
        percentile = int(round((total_players - rank) / total_players, 2) * 100)

    return rank, percentile


def get_percentile_color(percentile: int) -> tuple[float, float, float]:
    """
    Get a normalized RGB color based on the percentile rank.
    0%   -> Red (255, 0, 0)
    25%  -> Orange (255, 165, 0)
    50%  -> Yellow (255, 255, 0)
    75%  -> Light Green (144, 238, 144)
    100% -> Dark Green (0, 128, 0)

    :param percentile: an int of the percentile to get the color for
    :return: a tuple containing normalized RGB values that correspond to the given percentile
    """

    if percentile <= 25:
        # Interpolate between red (255,0,0) and orange (255,165,0)
        ratio = percentile / 25
        r = 255
        g = int(165 * ratio)
        b = 0
    elif percentile <= 50:
        # Interpolate between orange (255,165,0) and yellow (255,255,0)
        ratio = (percentile - 25) / 25
        r = 255
        g = 165 + int(90 * ratio)
        b = 0
    elif percentile <= 75:
        # Interpolate between yellow (255,255,0) and light green (144,238,144)
        ratio = (percentile - 50) / 25
        r = 255 - int((255 - 144) * ratio)
        g = 255 - int((255 - 238) * ratio)
        b = int(144 * ratio)
    else:
        # Interpolate between light green (144,238,144) and dark green (0,128,0)
        ratio = (percentile - 75) / 25
        r = 144 - int(144 * ratio)
        g = 238 - int((238 - 128) * ratio)
        b = 144 - int(144 * ratio)

    return (r / 255, g / 255, b / 255)


def get_prev_season(cur_season: str) -> str:
    """
    Get the str for previous season from a given season's str.

    :param cur_season: a str of the current season ('YYYY-YYYY')
    :return: a str of the season previous to the current season
    """

    start_year, end_year = map(int, cur_season.split("-"))
    prev_season = f"{start_year - 1}-{end_year - 1}"

    return prev_season


def get_player_header_row(player_name: str, season: str, pos: str) -> pd.Series:
    """
    Get a Series containing all the information needed for the player card's header.
    
    :param player_name: a str of the player's full name name that the Series is being retrieved for ('First Last')
    :param season: a str of the season to get the hearer information (YYYY-YYYY')
    :param pos: a str of the player's position's first letter ('f', 'd', or 'g')
    :return: a Series containing all the header information
    """
    if pos == 'g':
        all_player_profiles = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_profiles/{season}_goalie_profiles.csv')
        all_player_stats = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_all_goalie_stats.csv')

        player_profile_row = all_player_profiles[all_player_profiles['Player'] == player_name].copy()
        player_stats_row = all_player_stats[all_player_stats['Player'] == player_name].copy()
        player_stats_row = player_stats_row[['Player', 'GP', 'SV%', 'GAA']]

        player_header_row = pd.merge(player_profile_row, player_stats_row, on=['Player'])

    else:
        all_player_profiles = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_profiles/{season}_skater_profiles.csv')
        all_player_stats = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_all_skater_stats.csv')

        player_profile_row = all_player_profiles[all_player_profiles['Player'] == player_name].copy()
        player_stats_row = all_player_stats[all_player_stats['Player'] == player_name].copy()
        player_stats_row = player_stats_row[['Player', 'GP', 'TOI', 'Goals', 'Total Assists', 'Total Points']]

        player_header_row = pd.merge(player_profile_row, player_stats_row, on=['Player'])


    # Add Season column
    player_header_row['Season'] = season

    player_header_row['Position'] = player_header_row['Position'].replace({'R': 'RW', 'L': 'LW'})
    player_header_row['Team'] = player_header_row['Team'].replace({'L.A': 'LAK', 'S.J': 'SJS', 'N.J': 'NJD', 'T.B': 'TBL'})

    return player_header_row.iloc[0]


def get_total_players(season_data: pd.DataFrame, attribute: str ='all', pos: str = 'f') -> int:
    """
    Get the total amount of players that qualify for the given attribute rank 
    (some players are not given a rank for power play, penalty kill, or faceoffs).

    :param season_data: a DataFrame of player stats
    :param attribute: a str of the attribute to get the total players for
    :param pos: a str of the player's position's first letter ('f', 'd', or 'g')
    :return: an int of the total players that are included in an attribute
    """
    
    if attribute == 'all' or pos == 'g':
        total_players = len(season_data)
    else:
        score_column = f"{attribute}_score"
        total_players = (season_data[score_column] != -999999).sum()
    
    return total_players


def get_yearly_total_players(season: str, cur_season_data: pd.DataFrame, pos: str, years_num: int=5) -> dict[str, int]:
    """
    Get the total number of players for multiple past seasons based on different attributes.

    :param season: a str of the most recent season ('YYYY-YYYY')
    :param cur_season_data: a DataFrame containing player stats for the given season
    :param pos: a str of the player's position's first letter ('f', 'd', or 'g')
    :param years_num: an int specifying the number of past seasons to retrieve player totals for (default is 5)
    :return: a dict mapping attribute-year keys to the corresponding total number of players
    """
    yearly_total_players = {}
    tot_players_season = season
    tot_players_season_data = cur_season_data

    if pos == 'g':
        attribute_list = ['all']
        position_str = 'goalie'
    elif pos == 'f':
        attribute_list = ['all', 'ppl', 'pkl', 'fof']
        position_str = 'forward'
    elif pos == 'd':
        attribute_list = ['all', 'ppl', 'pkl', 'fof']
        position_str = 'defense'

    for _ in range(years_num):
        for attribute in attribute_list:
            yearly_total_players.update({f'{attribute}_{tot_players_season}': get_total_players(tot_players_season_data, attribute, pos)})
        
        tot_players_season = get_prev_season(tot_players_season)
        try:
            tot_players_season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/{position_str}_rankings/{tot_players_season}_{pos}_rankings.csv')
        except FileNotFoundError:
            print(f'Warning: Data for {tot_players_season} not found. Stopping iteration.')
            break

    return yearly_total_players


def get_player_multiple_seasons(player_name: str, cur_season: str, pos: str, seasons_num: int = 5) -> pd.DataFrame:
    """
    Get a DataFrame of a player's rankings for multiple consecutive seasons.

    :param player_name: A str of the full name of the player to get the multiple seasons for ('First Last')
    :param cur_season: A str of the most recent season ('YYYY-YYYY')
    :param pos: a str of the player's position's first letter ('f', 'd', or 'g')
    :param seasons_num: An int of the number of past seasons to include (default is 5)
    :return: A DataFrame containing player stats and total player counts over the specified seasons
    """

    if pos == 'g':
        position_str = 'goalie'
    elif pos == 'd':
        position_str = 'defense'
    elif pos == 'f':
        position_str = 'forward'


    # Load the current season's data
    season_zero_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/{position_str}_rankings/{cur_season}_{pos}_rankings.csv')
    
    # Get player row
    player_seasons = season_zero_data[season_zero_data['Player'] == player_name].copy()

    # Initialize previous season and total players dictionary
    prev_season = get_prev_season(cur_season)
    yearly_total_players = get_yearly_total_players(cur_season, season_zero_data, pos, seasons_num)

    # Add total players stats for the current season
    player_seasons['all_players'] = yearly_total_players.get(f'all_{cur_season}', 0)

    if pos == 'g':
        player_seasons['ppl_players'] = yearly_total_players.get(f'ppl_{cur_season}', 0)
        player_seasons['pkl_players'] = yearly_total_players.get(f'pkl_{cur_season}', 0)
        player_seasons['fof_players'] = yearly_total_players.get(f'fof_{cur_season}', 0)
    

    # Loop to get previous seasons
    for _ in range(seasons_num - 1):
        try:
            season_data = pd.read_csv(f'{DATA_DIR}/data/player_rankings/{position_str}_rankings/{prev_season}_{pos}_rankings.csv')
        except FileNotFoundError:
            print(f"Warning: Data for {prev_season} not found. Skipping this season.")
            break

        player_row = season_data[season_data['Player'] == player_name]
        if not player_row.empty:
            # Add player row to the DataFrame
            player_row = player_row.copy()
            player_row['all_players'] = yearly_total_players.get(f'all_{prev_season}', 0)
            if pos != 'g':
                player_row['ppl_players'] = yearly_total_players.get(f'ppl_{prev_season}', 0)
                player_row['pkl_players'] = yearly_total_players.get(f'pkl_{prev_season}', 0)
                player_row['fof_players'] = yearly_total_players.get(f'fof_{prev_season}', 0)
            player_seasons = pd.concat([player_seasons, player_row], ignore_index=True)

        # Move to the next previous season
        prev_season = get_prev_season(prev_season)

    return player_seasons

