# ====================================================================================================
# FUNCTIONS FOR GETTING ALL DATA USED IN PLAYER CARDS
# ====================================================================================================

# Imports
import pandas as pd
from datetime import datetime, date
from player_card_project import data_io
from player_card_project import constants



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
        games_played_percent = games_played / total_games

        if games_played_percent >= 0.60:
            role = 'Starter'
        elif games_played_percent >= 0.50:
            role = 'Tandem (1A)'
        elif games_played_percent >= 0.40:
            role = 'Tandem (1B)'
        elif games_played_percent >= 0.10:
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
    :return: An int of the player's age at the beginning of the given season
    """

    past_season = player_row['Season']
    date_of_birth = player_row['Date of Birth']

    # Get the birthday into a date object
    birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()

    # Get the start date of the season (September 1st of the first year)
    season_start_year = int(past_season.split("-")[0])
    season_date = date(season_start_year, 9, 1)

    # Calculate the player's age
    age = season_date.year - birth_date.year

    # Adjust if birthday hasn’t occurred yet by Sept 1
    if (birth_date.month, birth_date.day) > (season_date.month, season_date.day):
        age -= 1

    return age


def load_multi_season_data(cur_season: str, position: str, seasons_num: int = 5) -> tuple:
    """
    Load yearly (unweighted) rankings data for multiple seasons.

    :param cur_season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param seasons_num: An int of how many seasons to include (default is 5)
    :return: A tuple containing a list of seasons and a dictionary mapping season to DataFrame with percentiles
    """

    # Build list of seasons (newest to oldest)
    seasons = [cur_season]
    for _ in range(seasons_num - 1):
        seasons.append(data_io.get_prev_season(seasons[-1]))

    # Reverse the order is (oldest to newest for graphing)
    seasons.reverse()

    season_dfs = {}

    # For each season load yearly rankings
    for season in seasons:
        try:
            season_dfs[season] = data_io.load_rankings_csv(season, position, weighted=False)
        # Skip missing seasons
        except FileNotFoundError:
            continue

    return seasons, season_dfs


def make_history_columns(cur_df: pd.DataFrame, seasons: list, season_dfs: dict, position: str) -> pd.DataFrame:
    """
    Build multi-season history columns for player attribute percentiles and teams.

    :param cur_df: A DataFrame containing current season player data
    :param seasons: A list of seasons (oldest to newest)
    :param season_dfs: A dictionary mapping seasons to yearly ranking DataFrames with percentile data
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: A DataFrame with added attribute history and team history columns
    """
    cur_df = cur_df.copy()

    # Attributes to make percentile histories for
    if position != 'G':
        attributes = ['ovr', 'evo', 'evd']
    else:
        attributes = ['ovr', 'evs', 'pkl']

    # Make empty attribute history lists
    for attribute in attributes:
        cur_df[f"{attribute}_history"] = [[] for _ in range(len(cur_df))]

    # Make empty team history lists
    cur_df["team_history"] = [[] for _ in range(len(cur_df))]

    # Fill history lists
    for season in seasons:
        season_df = season_dfs.get(season)

        # Add attribute history
        for attribute in attributes:
            pct_col = f"{attribute}_pct"

            if season_df is not None and pct_col in season_df.columns:
                mapping = {
                    player_id: (None if pd.isna(value) else int(value))
                    for player_id, value in zip(season_df['Player ID'], season_df[pct_col])
                }
            else:
                mapping = {}

            cur_df[f"{attribute}_history"] = cur_df.apply(
                lambda row: row[f"{attribute}_history"] + [mapping.get(row['Player ID'], None)],
                axis=1
            )

        # Add team history
        if season == seasons[-1]:
            team_mapping = dict(zip(cur_df['Player ID'], cur_df['Team']))
        else:
            try:
                team_df = data_io.load_card_data_csv(season, position)
                team_mapping = dict(zip(team_df['Player ID'], team_df['Team']))
            except FileNotFoundError:
                team_mapping = {}

        cur_df["team_history"] = cur_df.apply(
            lambda row: row["team_history"] + [team_mapping.get(row['Player ID'], None)],
            axis=1
        )

    return cur_df


def make_card_data(season: str, position: str) -> None:
    """
    Generate a CSV file of all the relevant player card data from other CSV files.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: None
    """

    # Load data
    all_stats_df = data_io.load_stats_csv(season, position, 'all')
    ev_stats_df = data_io.load_stats_csv(season, position, '5v5')
    rankings_df = data_io.load_rankings_csv(season, position)
    player_ids_df = data_io.load_player_ids_csv(season)
    if position == 'G':
        logs_df = data_io.load_goalie_logs_csv(season)
    bios_df = data_io.load_player_bios_csv()

    # Rename certain columns
    bios_cols = bios_df[[
        'Player ID', 'Height (in)', 'Weight (lb)', 'Birth Date', 'Birth Country',
        'Draft Year', 'Draft Round', 'Draft Overall Pick', 'Shoots Catches',
    ]].rename(columns={
        'Weight (lb)': 'Weight (lbs)',
        'Birth Date': 'Date of Birth',
        'Draft Overall Pick': 'Overall Draft Position',
    })

    # Get stats, percentiles, ranks, and total players
    if position != 'G':
        all_stats_cols = all_stats_df[['Player ID', 'GP', 'TOI', 'Goals', 'Total Assists', 'Total Points', 'ixG']].copy()
        ev_stats_cols = ev_stats_df[['Player ID', 'GF%', 'xGF%']].copy()

        attrs = ['ovr', 'evo', 'evd', 'ppl', 'pkl', 'fin', 'gol', 'xgl', 'ast', 'pen', 'hit', 'ozs', 'pdo', 'tmt', 'cmp']
        pct_cols = [f'{attr}_pct' for attr in attrs]
        rank_cols = [f'{attr}_rank' for attr in attrs]
        players_cols = ['all_players', 'ppl_players', 'pkl_players']

        rankings_cols = rankings_df[['Season', 'Player ID', 'Player', 'Team', 'Position'] + pct_cols + rank_cols + players_cols]

    else:
        all_stats_cols = all_stats_df[['Player ID', 'GP', 'TOI', 'SV%', 'GAA', 'xG Against', 'Goals Against']].copy()

        attrs = ['ovr', 'evs', 'pkl', 'ldg', 'mdg', 'hdg', 'rbd', 'tmd', 'gre', 'qal', 'bad', 'awf', 'wrk']
        pct_cols = [f'{attr}_pct' for attr in attrs]
        rank_cols = [f'{attr}_rank' for attr in attrs]
        players_cols = ['all_players']

        rankings_cols = rankings_df[['Season', 'Player ID', 'Player', 'Team', 'Position'] + pct_cols + rank_cols + players_cols]

    # Merge all data
    card_info_df = rankings_cols.merge(all_stats_cols, on='Player ID', how='left')
    if position != 'G':
        card_info_df = card_info_df.merge(ev_stats_cols, on='Player ID', how='left')

    # Add specific position column
    specific_position = player_ids_df[['Player ID', 'Specific Position']].drop_duplicates(subset='Player ID')
    card_info_df = card_info_df.merge(specific_position, on='Player ID', how='left')

    card_info_df = card_info_df.merge(bios_cols, on='Player ID', how='left')

    # For goalies add their record stats from goalie logs
    if position == 'G':
        logs_df = logs_df.copy()
        logs_df['Result'] = logs_df['Result'].fillna('')

        # Get game results ('W', 'L', 'O') and shutouts
        record_df = (logs_df.groupby('Player ID')['Result'].value_counts().unstack(fill_value=0))
        shutout_df = (logs_df.groupby('Player ID')['Shutouts'].sum().reset_index())

        # Rename 'O' to 'OT/SO'
        record_df = (record_df.rename(columns={'O': 'OT/SO'}).reset_index())

        # Merge the record stats into the main card data DataFrame
        card_info_df = card_info_df.merge(record_df[['Player ID', 'W', 'L', 'OT/SO']], on='Player ID', how='left')
        card_info_df = card_info_df.merge(shutout_df[['Player ID', 'Shutouts']], on='Player ID', how='left')

        # Fill any NaN values with 0
        card_info_df[['W', 'L', 'OT/SO', 'Shutouts']] = (card_info_df[['W', 'L', 'OT/SO', 'Shutouts']].fillna(0).astype(int))

    # Replace Age column with season-specific age
    card_info_df['Age'] = card_info_df.apply(get_player_age, axis=1)

    # Add player role
    card_info_df['Role'] = card_info_df.apply(get_player_role, axis=1)
    cols = list(card_info_df.columns)
    cols.remove('Role')
    stats_start = cols.index("GP")
    cols = cols[:stats_start] + ["Role"] + cols[stats_start:]
    card_info_df = card_info_df[cols]

    # Add previous five season main attribute percentiles
    seasons, season_dfs = load_multi_season_data(season, position)
    card_info_df = make_history_columns(card_info_df, seasons, season_dfs, position)

    # Sort based on player name
    card_info_df = card_info_df.sort_values('Player').reset_index(drop=True)

    # Round key stat columns
    two_decimal_cols = ['ixG', 'GF%', 'xGF%', 'TOI', 'GAA', 'xG Against']
    three_decimal_cols = ['SV%']
    for col in two_decimal_cols:
        if col in card_info_df.columns:
            card_info_df[col] = card_info_df[col].round(2)
    for col in three_decimal_cols:
        if col in card_info_df.columns:
            card_info_df[col] = card_info_df[col].round(3)

    # Save CSV file
    pos_folder = constants.POSITION_FOLDERS[position]
    filename = f'{season}_{position}_card_data.csv'
    data_io.save_csv(card_info_df, 'card_data', pos_folder, filename)

