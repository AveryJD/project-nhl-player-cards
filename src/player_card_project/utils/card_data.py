# ====================================================================================================
# FUNCTIONS FOR GETTING ALL DATA USED IN PLAYER CARDS
# ====================================================================================================

# Imports
import pandas as pd
from datetime import datetime, date
from player_card_project.utils import load_save as file
from player_card_project.utils import constants


def resolve_team(player_row: pd.Series) -> str:
    """
    Determines the player's last played for team in a season
    :param player_row: A Series containing player data
    :return: A str of the last played for team
    """
    # Split the player's teams
    teams = str(player_row['Team']).split(', ')
    # If there is only one team or no API team, the one team is the correct one
    if len(teams) == 1 or pd.isna(player_row['Team_api']):
        team = teams[0]
    # Else the API team is the correct one
    else:
        team = player_row['Team_api']
    return team


def get_player_role(player_row: pd.Series) -> str:
    """
    Determines the player's role based on a player's time on ice allocation and games played.

    :param player_row: A Series containing player data
    :return: A str of the toi allocation
    """
    # Player roles for goalies
    if player_row['Position'] == 'G':
        games_played = player_row['GP']
        total_games = constants.SEASON_GAMES[player_row['Season']]
        games_played_percet = games_played / total_games

        if games_played_percet >= 0.60:
            role = 'Starter'
        elif games_played_percet >= 0.50:
            role = 'Tandem (1A)'
        elif games_played_percet >= 0.40:
            role = 'Tandem (1B)'
        elif games_played_percet >= 0.10:
            role = 'Backup'
        else:
            role = 'Fringe'

    # Player roles for defensemen
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

    # Player roles for forwards
    else:
        avg_toi = player_row['TOI'] / player_row['GP']
        if avg_toi >= 18.0:
            role = 'First Line'
        elif avg_toi > 15.5:
            role = 'Second Line'
        elif avg_toi > 13.5:
            role = 'Third Line'
        elif avg_toi > 9.0:
            role = 'Fourth Line'
        else:
            role = 'Fringe'

    return role


def get_player_age(player_row: pd.Series) -> int:
    """
    Calculates the player's age on September 1st of the first year of the given season.

    :param player_row: A Series containing player data
    :return: An int of the player's age at the begining of the given season
    """

    past_season = player_row['Season']
    date_of_birth = player_row['Date of Birth']

    # Get the birthday into a date object
    birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()

    # Get the start date of the season (Sptember 1st of the first year)
    season_start_year = int(past_season.split("-")[0])
    season_date = date(season_start_year, 9, 1)

    # Calculate the player's age
    age = season_date.year - birth_date.year
    
    # Adjust if birthday hasn’t occurred yet by Sept 1
    if (birth_date.month, birth_date.day) > (season_date.month, season_date.day):
        age -= 1

    return age


def add_percentiles(df: pd.DataFrame, pos: str) -> pd.DataFrame:
    """
    Add percentile rankings for key attributes based on player ranks.

    :param df: A DataFrame containing player rankings for a given season
    :param pos: A str of the player's position ('F', 'D', or 'G')
    :return: A DataFrame with additional percentile columns for each attribute
    """
    df = df.copy()

    # Select important attributes based on position
    if pos != 'G':
        attributes = ['evo', 'evd', 'ppl', 'pkl']
    else:
        attributes = ['all', 'evs', 'gpk']

    for attribute in attributes:
        rank_col = f"{attribute}_rank"

        # For certain attributes, only include valid players
        if attribute in ['ppl', 'pkl', 'fof'] and pos != 'G':
            total_players = df[rank_col].notna().sum()
        else:
            total_players = len(df)

        # Percentile calculation
        pct_col = f"{attribute}_pct"
        df[pct_col] = ((total_players - df[rank_col]) / total_players * 100).round().astype('Int64')

        # Set any invalid players to NA
        df.loc[df[rank_col].isna(), pct_col] = pd.NA

    return df


def load_multi_season_data(cur_season: str, pos: str, seasons_num: int = 5):
    """
    Load ranking data and compute percentiles for multiple seasons.

    :param cur_season: A str of the most recent season ('YYYY-YYYY')
    :param pos: A str of the player's position ('F', 'D', or 'G')
    :param seasons_num: An int of how many seasons to include (default is 5)
    :return: A tuple containing a list of seasons and a dictionary mapping season to DataFrame with percentiles
    """

    # Build list of seasons (newest to oldest)
    seasons = [cur_season]
    for _ in range(seasons_num - 1):
        seasons.append(file.get_prev_season(seasons[-1]))

    # Reverse the order is (oldest to newest for graphing)
    seasons.reverse()

    season_dfs = {}

    # For each season load yearly rankings and calculate percentiles
    for season in seasons:
        try:
            df = file.load_rankings_csv(season, pos, weighted=False)
            df = add_percentiles(df, pos)
            season_dfs[season] = df
        # Skip missing seasons
        except FileNotFoundError:
            continue

    return seasons, season_dfs


def make_history_columns(cur_df: pd.DataFrame, seasons: list, season_dfs: dict, pos: str) -> pd.DataFrame:
    """
    Build multi-season history columns for player attribute percentiles and teams.

    :param cur_df: A DataFrame containing current season player data
    :param seasons: A list of seasons (oldest to newest)
    :param season_dfs: A dictionary mapping seasons to yearly ranking DataFrames with percentile data
    :param pos: A str of the player's position ('F', 'D', or 'G')
    :return: A DataFrame with added attribute history and team history columns
    """
    cur_df = cur_df.copy()

    if pos != 'G':
        attributes = ['evo', 'evd', 'ppl', 'pkl']
    else:
        attributes = ['all', 'evs', 'gpk']

    for attribute in attributes:
        cur_df[f"{attribute}_history"] = [[] for _ in range(len(cur_df))]

    cur_df["team_history"] = [[] for _ in range(len(cur_df))]

    for season in seasons:
        if season not in season_dfs:
            continue

        season_df = season_dfs[season]

        # Attribute history comes from yearly ranking data
        for attribute in attributes:
            pct_col = f"{attribute}_pct"
            mapping = {
                player: (None if pd.isna(value) else int(value))
                for player, value in zip(season_df['Player'], season_df[pct_col])
            }

            cur_df[f"{attribute}_history"] = cur_df.apply(
                lambda row: row[f"{attribute}_history"] + [mapping.get(row['Player'], None)],
                axis=1
            )

        # Add current team
        if season == seasons[-1]:
            team_mapping = dict(zip(cur_df['Player'], cur_df['Team']))
        # Add team history
        else:
            try:
                team_df = file.load_card_data_csv(season, pos)
                team_mapping = dict(zip(team_df['Player'], team_df['Team']))
            except FileNotFoundError:
                team_mapping = {}

        cur_df["team_history"] = cur_df.apply(
            lambda row: row["team_history"] + [team_mapping.get(row['Player'], None)],
            axis=1
        )

    return cur_df


def make_card_data(season, position) -> None:
    """
    Generate a CSV file of all the relevent player card data from other CSV files
    
    :param season: A str of the season to make the card data for ('YYYY-YYYY')
    :param position: A str of the player's position's first letter to make the card data for ('F', 'D', or 'G')
    :return: None
    """

    # Load data
    bios_df = file.load_bios_csv(season, position)
    all_stats_df = file.load_stats_csv(season, position, 'all')
    ev_stats_df = file.load_stats_csv(season, position, '5v5')
    rankings_df = file.load_rankings_csv(season, position)
    ids_df = file.load_ids_csv(season)
    if position == 'G':
        logs_df = file.load_goalie_logs_csv(season)

    # Select important columns
    bios_cols = bios_df[['Player', 'Team', 'Position', 'Age', 'Date of Birth', 'Birth Country', 
                         'Nationality', 'Height (in)', 'Weight (lbs)', 
                         'Draft Year', 'Draft Round', 'Overall Draft Position']]  

    if position != 'G':
        all_stats_cols = all_stats_df[['Player', 'Team', 'Position', 'GP', 'TOI', 'Goals', 'Total Assists', 'Total Points', 'ixG']].copy()
        ev_stats_cols = ev_stats_df[['Player', 'Team', 'Position', 'GF%', 'xGF%',]].copy()

        rankings_cols = rankings_df[['Season', 'Player', 'Team', 'Position', 
                                     'evo_rank', 'evd_rank', 'ppl_rank', 'pkl_rank', 
                                     'oio_rank', 'oid_rank', 'sht_rank', 'scr_rank', 'plm_rank',
                                     'zon_rank','pen_rank', 'phy_rank', 'fof_rank', 'fan_rank']]
        
    else:
        all_stats_cols = all_stats_df[['Player', 'Team', 'GP', 'TOI', 'SV%', 'GAA', 'xG Against', 'Goals Against']].copy()
        ev_stats_cols = ev_stats_df[['Player', 'Team']].copy()
        all_stats_cols['Position'] = 'G'
        ev_stats_cols['Position'] = 'G'

        rankings_cols = rankings_df[['Season', 'Player', 'Team', 'Position', 
                                     'all_rank', 'evs_rank', 'gpk_rank', 
                                     'ldg_rank', 'mdg_rank', 'hdg_rank', 'rbd_rank', 'tmd_rank',
                                    'gre_rank', 'qal_rank', 'bad_rank', 'awf_rank', 'fan_rank']]

    # Merge all data
    card_info_df = rankings_cols.merge(
        all_stats_cols, on=['Player', 'Team', 'Position'], how='left'
    ).merge(
        ev_stats_cols, on=['Player', 'Team', 'Position'], how='left'
    ).merge(
        bios_cols, on=['Player', 'Team', 'Position'], how='left'
    ).merge(
        ids_df[['Player', 'Position', 'Player ID', 'Team']],
        on=['Player', 'Position'],
        how='left',
        suffixes=('', '_api')
    )

    # For goalies get their record stats
    if position == 'G':
        logs_df = logs_df.copy()
        logs_df['Result'] = logs_df['Result'].fillna('')

        # Get game results ('W', 'L', 'O')
        record_df = (logs_df
            .groupby('Player')['Result']
            .value_counts()
            .unstack(fill_value=0)
        )

        # Get shutouts
        shutout_df = (logs_df
            .groupby('Player')['Shutouts']
            .sum()
            .reset_index()
        )

        # Rename 'O' (OT/SO loss) to 'OT/SO'
        record_df = (record_df
            .rename(columns={'O': 'OT/SO'})
            .reset_index()
        )

        # Merge the record stats into the main card data DataFrame
        card_info_df = card_info_df.merge(
            record_df[['Player', 'W', 'L', 'OT/SO']],
            on='Player',
            how='left'
        )

        card_info_df = card_info_df.merge(
            shutout_df[['Player', 'Shutouts']],
            on='Player',
            how='left'
        )

        # Fill any NaN values with 0
        card_info_df[['W', 'L', 'OT/SO', 'Shutouts']] = (
            card_info_df[['W', 'L', 'OT/SO', 'Shutouts']]
            .fillna(0)
            .astype(int)
        )

    # Fallback for missing team values
    card_info_df['Team'] = card_info_df.apply(resolve_team, axis=1)
    card_info_df.drop(columns=['Team_api'], inplace=True, errors='ignore')

    # Replace Age column with season-specific age
    card_info_df['Age'] = card_info_df.apply(get_player_age, axis=1)

    # Add player role
    card_info_df['Role'] = card_info_df.apply(get_player_role, axis=1)
    cols = list(card_info_df.columns)
    cols.remove("Role")
    stats_start = cols.index("GP")
    cols = cols[:stats_start] + ["Role"] + cols[stats_start:]
    card_info_df = card_info_df[cols]

    # Add previous five season main attribute percentiles
    seasons, season_dfs = load_multi_season_data(season, position)
    card_info_df = make_history_columns(card_info_df, seasons, season_dfs, position)

    # Sort based on player name
    card_info_df = card_info_df.sort_values('Player').reset_index(drop=True)

    # Save CSV file
    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    filename = f'{season}_{position}_card_data.csv'
    file.save_csv(card_info_df, 'card_data', pos_folder, filename)

