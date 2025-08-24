# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import rank_scores as rs
from utils import load_save as file
from utils import constants


def calculate_player_scores(position: str, all_df: pd.DataFrame, evs_df: pd.DataFrame, pkl_df: pd.DataFrame, ppl_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate player scores for all attributes.

    :param position: a str representing the player's position ('F', 'D', or 'G')
    :param all_df: a DataFrame containing the players stats from all situations
    :param evs_df: a DataFrame containing the players 5v5 stats
    :param pkl_df: a DataFrame containing the players 4v5 stats
    :param ppl_df: a DataFrame containing the players 5v4 stats (default is None to account for goalies)
    :return: None
    """

    skater_scorer = rs.SkaterScorer()
    goalie_scorer = rs.GoalieScorer()

    # Calculate skater scores
    if position != 'G':
        scores = pd.DataFrame({
            'evo_score': skater_scorer.offensive_score(evs_df),
            'evd_score': skater_scorer.defensive_score(evs_df),
            'ppl_score': skater_scorer.offensive_score(ppl_df),
            'pkl_score': skater_scorer.defensive_score(pkl_df),
            'oio_score': skater_scorer.oniceoffense_score(evs_df),
            'oid_score': skater_scorer.onicedefense_score(evs_df),
            'sht_score': skater_scorer.shooting_score(all_df),
            'scr_score': skater_scorer.scoring_score(all_df),
            'zon_score': skater_scorer.ozonestarts_score(evs_df),
            'plm_score': skater_scorer.playmaking_score(all_df),
            'pen_score': skater_scorer.penalties_score(all_df),
            'phy_score': skater_scorer.physicality_score(all_df),
            'fof_score': skater_scorer.faceoff_score(all_df),
            'fan_score': skater_scorer.fantasy_score(all_df, ppl_df, pkl_df),
        }, index=all_df.index)

    # Calculate goalie scores
    else:
        scores = pd.DataFrame({
            'all_score': goalie_scorer.total_score(all_df),
            'evs_score': goalie_scorer.total_score(evs_df),
            'gpk_score': goalie_scorer.total_score(pkl_df),
            'ldg_score': goalie_scorer.zone_score(all_df, 'LD'),
            'mdg_score': goalie_scorer.zone_score(all_df, 'MD'),
            'hdg_score': goalie_scorer.zone_score(all_df, 'HD'),
        }, index=all_df.index)

    return scores


def make_player_rankings(season: str, position: str) -> None:
    """
    Generate player rankings for a specific season.

    :param season: a str representing the season ('YYYY-YYYY')
    :param position: a str representing the player's position ('F', 'D', or 'G')
    :return: None
    """

    # For skaters
    if position != 'G':
        # Load all skater data
        all_data = file.load_stats_csv(season, position, 'all')
        evs_data = file.load_stats_csv(season, position, '5v5')
        ppl_data = file.load_stats_csv(season, position, '5v4')
        pkl_data = file.load_stats_csv(season, position, '4v5')

        all_data = all_data.set_index(['Player', 'Team'])
        evs_data = evs_data.set_index(['Player', 'Team'])
        ppl_data = ppl_data.set_index(['Player', 'Team'])
        pkl_data = pkl_data.set_index(['Player', 'Team'])

        # Filter skaters who do not meet the minimum games played requirement
        season_games = constants.SEASON_GAMES[season]
        min_gp = season_games * 0.25
        valid_players = all_data.loc[all_data['GP'] >= min_gp].index

        all_data = all_data.loc[valid_players]

        # Ensure all DataFrames share the same index
        common_index = all_data.index
        evs_data = evs_data.reindex(common_index).fillna(0)
        ppl_data = ppl_data.reindex(common_index).fillna(0)
        pkl_data = pkl_data.reindex(common_index).fillna(0)

        # Filter skaters who meet the minimum special teams TOI requirement
        valid_ppl_players = ppl_data.loc[ppl_data['TOI'] >= season_games * 0.75].index
        valid_pkl_players = pkl_data.loc[pkl_data['TOI'] >= season_games * 0.75].index

        # Boolean masks of invalid players (now aligned with common_index)
        invalid_ppl = ~ppl_data.index.isin(valid_ppl_players)
        invalid_pkl = ~pkl_data.index.isin(valid_pkl_players)

        # Calculate skater scores
        scores_df = calculate_player_scores(position, all_data, evs_data, pkl_data, ppl_data)

        # Mask invalid PP/PK players' scores
        scores_df.loc[invalid_ppl, 'ppl_score'] = -999999
        scores_df.loc[invalid_pkl, 'pkl_score'] = -999999

        # Put together scores DataFrame
        rankings = all_data.reset_index()[['Player', 'Team', 'Position']].copy()
        rankings = rankings.set_index(['Player', 'Team'])
        rankings = pd.concat([rankings, scores_df], axis=1)
        rankings = rankings.reset_index()
        rankings.insert(0, 'Season', season)

    # For goalies
    else:
        # Load all goalie data
        all_data = file.load_stats_csv(season, 'G', 'all')
        evs_data = file.load_stats_csv(season, 'G', '5v5')
        pkl_data = file.load_stats_csv(season, 'G', '4v5')

        all_data = all_data.set_index(['Player', 'Team'])
        evs_data = evs_data.set_index(['Player', 'Team'])
        pkl_data = pkl_data.set_index(['Player', 'Team'])

        # Filter goalies who do not meet the minimum games played requirement (15% of games played over the season)
        min_gp = constants.SEASON_GAMES[season] * 0.15
        valid_players = all_data.loc[all_data['GP'] >= min_gp].index

        all_data = all_data.loc[valid_players]
        evs_data = evs_data.loc[valid_players]
        pkl_data = pkl_data.loc[valid_players]

        # Calculate goalie scores
        scores_df = calculate_player_scores(position, all_data, evs_data, pkl_data)

        # Put together scores DataFrame
        rankings = all_data.reset_index()[['Player', 'Team']].copy()
        rankings.insert(2, 'Position', 'G')
        rankings = rankings.set_index(['Player', 'Team'])
        rankings = pd.concat([rankings, scores_df], axis=1)
        rankings = rankings.reset_index()
        rankings.insert(0, 'Season', season)


    # Rank player scores
    score_columns = [col for col in scores_df.columns if col.endswith('_score')]
    for col in score_columns:
        attr = col.split('_')[0]
        rankings[f'{attr}_rank'] = rankings[col].rank(ascending=False, method='dense')

    # Save rankings CSV file
    if position == 'F':
        pos_folder = 'forwards' 
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    filename = f'{season}_{position}_yearly_rankings.csv'
    file.save_csv(rankings, 'rankings', f'yearly_{pos_folder}', filename)


def make_player_weighted_rankings(season: str, position: str):
    """
    Generate weighted player rankings for a specific season.

    :param season: a str representing the season ('YYYY-YYYY')
    :param position: a str representing the player's position ('F', 'D', or 'G')
    :return: None
    """

    # Get the season strings for the two previous seasons
    prev_season = file.get_prev_season(season)
    prev_prev_season = file.get_prev_season(prev_season)

    # Get the csv files containing the player rankings/scores
    cur_rankings = file.load_rankings_csv(season, position, weighted=False)
    prev_rankings = file.load_rankings_csv(prev_season, position, weighted=False)
    prev_prev_rankings = file.load_rankings_csv(prev_prev_season, position, weighted=False)

    # Determine players to rank (those in the current season)
    rankings_players = cur_rankings[['Season', 'Player', 'Position', 'Team']].copy()

    # Determine the score columns
    score_cols = []
    for column in cur_rankings.columns:
        if column.endswith('_score'):
            score_cols.append(column)

    # Combine each seasons' rankings to get the min and max score per score column
    all_rankings = pd.concat([cur_rankings, prev_rankings, prev_prev_rankings], ignore_index=True)

    # Only normalize valid scores (exclude -999999)
    valid_all_rankings = all_rankings[all_rankings[score_cols[0]] != -999999]

    # Fit scaler
    scaler = MinMaxScaler()
    scaler.fit(valid_all_rankings[score_cols])

    # Transform each season's rankings using the same scaler
    scaled_cur_rankings = cur_rankings.copy()
    scaled_prev_rankings = prev_rankings.copy()
    scaled_prev_prev_rankings = prev_prev_rankings.copy()

    for df in [scaled_cur_rankings, scaled_prev_rankings, scaled_prev_prev_rankings]:
        mask_valid = df[score_cols[0]] != -999999
        df.loc[mask_valid, score_cols] = scaler.transform(df.loc[mask_valid, score_cols])

    # Initialized list to store weighted scores
    weighted_scores = []

    # For each player calculate their weighted scores
    for _, row in rankings_players.iterrows():
        name = row['Player']
        scores = {}

        # Get the scores fore each season
        row_cur = scaled_cur_rankings[scaled_cur_rankings['Player'] == name]
        if not scaled_prev_rankings.empty:
            row_prev = scaled_prev_rankings[scaled_prev_rankings['Player'] == name]
        else:
            row_prev = pd.DataFrame()
        if not scaled_prev_prev_rankings.empty:
            row_prev_prev = scaled_prev_prev_rankings[scaled_prev_prev_rankings['Player'] == name]
        else:
            row_prev_prev = pd.DataFrame()

        # Count how many seasons the player has scores for
        available_seasons = [df for df in [row_cur, row_prev, row_prev_prev] if not df.empty]
        num_seasons = len(available_seasons)

        # Get the weightings of the seasons depending on how many seasons the player has scores for
        if num_seasons == 3:
            weights = [0.50, 0.35, 0.15]
        elif num_seasons == 2:
            weights = [0.60, 0.30]
        elif num_seasons == 1:
            weights = [0.80]

        # Weight each different score attribute
        for col in score_cols:
            total_score = 0
            total_weight = 0
            for weight, df in zip(weights, available_seasons):
                val = df.iloc[0][col]
                if val != -999999:
                    total_score += val * weight
                    total_weight += weight
            if total_weight > 0:
                scores[col] = total_score
            else:
                scores[col] = -999999

        weighted_scores.append(scores)

    # Create the scores data frame
    scores_df = pd.DataFrame(weighted_scores)
    rankings = pd.concat([rankings_players.reset_index(drop=True), scores_df], axis=1)

    # Make the rankings for each score
    for col in score_cols:
        rankings[col] = rankings[col].replace(0, -999999)
        attr = col.split('_')[0]
        mask_exclude = (rankings[col] == -999999)
        scores_for_rank = rankings[col].mask(mask_exclude, other=pd.NA)
        rankings[f'{attr}_rank'] = scores_for_rank.rank(ascending=False, method='dense')

    # Save rankings CSV file
    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    filename = f'{season}_{position}_weighted_rankings.csv'
    file.save_csv(rankings, 'rankings', f'weighted_{pos_folder}', filename)
