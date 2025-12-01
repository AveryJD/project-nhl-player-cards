# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import scoring
from utils import constants
from utils import load_save as file


def calculate_player_scores(position: str, all_df: pd.DataFrame, evs_df: pd.DataFrame, pkl_df: pd.DataFrame, ppl_df: pd.DataFrame = None, goalie_logs_df=None) -> pd.DataFrame:
    """
    Calculate player scores for all attributes.

    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param all_df: A DataFrame containing the players stats from all situations
    :param evs_df: A DataFrame containing the players 5v5 stats
    :param pkl_df: A DataFrame containing the players 4v5 stats
    :param ppl_df: A DataFrame containing the players 5v4 stats (default is None to account for goalies)
    :param goalie_logs_df: A DataFrame containing the goalies game logs (default is None to account for skaters)
    :return: None
    """

    skater_scorer = scoring.SkaterScorer()
    goalie_scorer = scoring.GoalieScorer()

    # Calculate skater scores
    if position != 'G':
        scores = pd.DataFrame({
            'evo_score': skater_scorer.offensive_score(evs_df),
            'evd_score': skater_scorer.defensive_score(evs_df),
            'ppl_score': skater_scorer.offensive_score(ppl_df, is_ppl=True),
            'pkl_score': skater_scorer.defensive_score(pkl_df, is_pkl=True),
            'oio_score': skater_scorer.oniceoffense_score(evs_df),
            'oid_score': skater_scorer.onicedefense_score(evs_df),
            'sht_score': skater_scorer.shooting_score(evs_df),
            'scr_score': skater_scorer.scoring_score(evs_df),
            'plm_score': skater_scorer.playmaking_score(evs_df),
            'zon_score': skater_scorer.ozonestarts_score(evs_df),
            'pen_score': skater_scorer.penalties_score(evs_df),
            'phy_score': skater_scorer.physicality_score(evs_df),
            'fof_score': skater_scorer.faceoff_score(evs_df),
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
            'rbd_score': goalie_scorer.rebound_score(all_df),
            'tmd_score': goalie_scorer.team_d_score(all_df),
            'gre_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Great'),
            'qal_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Quality'),
            'bad_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Bad'),
            'awf_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Awful'),
            'fan_score': goalie_scorer.goalie_fantasy_score(all_df, goalie_logs_df),
        }, index=all_df.index)

    return scores


def make_player_rankings(season: str, position: str) -> None:
    """
    Generate player rankings for a specific season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
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
        min_games = constants.SEASON_GAMES[season] * constants.SKATER_MIN_GP
        valid_players = all_data.loc[all_data['GP'] >= min_games].index

        all_data = all_data.loc[valid_players]

        # Ensure all DataFrames share the same index
        common_index = all_data.index
        evs_data = evs_data.reindex(common_index).fillna(0)
        ppl_data = ppl_data.reindex(common_index).fillna(0)
        pkl_data = pkl_data.reindex(common_index).fillna(0)

        # Filter skaters who meet the minimum special teams TOI requirement and faceoffs taken requirement
        min_power_play = constants.SKATER_MIN_PP
        min_penalty_kill = constants.SKATER_MIN_PK
        valid_ppl_players = ppl_data.loc[ppl_data['TOI'] >= all_data['GP'] * min_power_play].index
        valid_pkl_players = pkl_data.loc[pkl_data['TOI'] >= all_data['GP'] * min_penalty_kill].index

        min_faceoffs = constants.SKATER_MIN_FO
        total_fo = all_data['Faceoffs Won'] + all_data['Faceoffs Lost']
        valid_fof_players = all_data.loc[total_fo >= all_data['GP'] * min_faceoffs].index

        # Boolean masks of invalid player scores
        invalid_ppl = ~ppl_data.index.isin(valid_ppl_players)
        invalid_pkl = ~pkl_data.index.isin(valid_pkl_players)
        invalid_fof = ~all_data.index.isin(valid_fof_players)

        # Calculate skater scores
        scores_df = calculate_player_scores(position, all_data, evs_data, pkl_data, ppl_df=ppl_data)

        # Mask invalid PP/PK players' scores
        scores_df.loc[invalid_ppl, 'ppl_score'] = -999999
        scores_df.loc[invalid_pkl, 'pkl_score'] = -999999
        scores_df.loc[invalid_fof, 'fof_score'] = -999999

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
        logs_data = file.load_goalie_logs_csv(season)

        all_data = all_data.set_index(['Player'])
        evs_data = evs_data.set_index(['Player'])
        pkl_data = pkl_data.set_index(['Player'])
        logs_data = logs_data.set_index(['Player'])

        # Filter goalies who do not meet the minimum games played requirement (15% of games played over the season)
        min_games = constants.SEASON_GAMES[season] * constants.GOALIE_MIN_GP
        valid_players = all_data.loc[all_data['GP'] >= min_games].index

        all_data = all_data.loc[valid_players]
        evs_data = evs_data.loc[valid_players]
        pkl_data = pkl_data.loc[valid_players]

        valid_log_players = all_data.index.get_level_values('Player')
        logs_data = logs_data.loc[valid_log_players]

        # Calculate goalie scores
        scores_df = calculate_player_scores(position, all_data, evs_data, pkl_data, goalie_logs_df=logs_data)

        # Put together scores DataFrame
        rankings = all_data.reset_index()[['Player', 'Team']].copy()
        rankings['Position'] = 'G'
        rankings = pd.concat([rankings, scores_df.reset_index(drop=True)], axis=1)
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

    filename = f'{season}_{position}_yearly_ranking.csv'
    file.save_csv(rankings, 'data_ranking', f'yearly_{pos_folder}', filename)


def make_player_weighted_rankings(season: str, position: str):
    """
    Generate weighted player rankings for a specific season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
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

    # Initialized list to store weighted scores
    weighted_scores = []

    # For each player calculate their weighted scores
    for _, row in rankings_players.iterrows():
        name = row['Player']
        scores = {}

        # Extract season rows (use None if missing)
        if not prev_prev_rankings.empty:
            row_prev_prev = prev_prev_rankings[prev_prev_rankings['Player'] == name]
        else:
            row_prev_prev = None

        if not prev_rankings.empty:
            row_prev = prev_rankings[prev_rankings['Player'] == name]
        else:
            row_prev = None
            row_prev_prev = None

        
        if not cur_rankings.empty:
            row_cur = cur_rankings[cur_rankings['Player'] == name]
        else:
            row_cur = None
            row_prev = None
            row_prev_prev = None

        # Maintain season order
        season_rows = [row_cur, row_prev, row_prev_prev]

        # Calculate weighted scores for each score column
        for col in score_cols:

            # Gather score values (keep None for missing)
            values = []
            for df in season_rows:
                if not df.empty:
                    value = df.iloc[0][col]
                    values.append(value if value != -999999 else None)
                else:
                    values.append(None)

            # If the player doesn't have scores for the current season, skip them
            if values[0] is None:
                scores[col] = -999999
                continue

            # Count valid seasons
            num_valid = sum(value is not None for value in values)

            # Select the proper weight vectors
            # All three seasons are present
            if num_valid == 3:
                weight_vector_pos = constants.THREE_SEASONS_WEIGHTS_POS
                weight_vector_neg = constants.THREE_SEASONS_WEIGHTS_NEG
            elif num_valid == 2:
            # The current and previous seasons are present
                if values[1] is not None:
                    weight_vector_pos = constants.TWO_SEASONS_WEIGHTS_POS
                    weight_vector_neg = constants.TWO_SEASONS_WEIGHTS_NEG
            # The current and previous-previous seasons are present
                else:
                    weight_vector_pos = constants.ONE_SEASON_WEIGHTS_POS
                    weight_vector_neg = constants.ONE_SEASON_WEIGHTS_NEG
                    values[2] = None
            # Only the current season is present
            elif num_valid == 1:
                weight_vector_pos = constants.ONE_SEASON_WEIGHTS_POS
                weight_vector_neg = constants.ONE_SEASON_WEIGHTS_NEG

            # Apply weights
            weighted_sum = 0

            for season_idx, current_value in enumerate(values):
                # If the player's current season value is None, skip them
                if current_value is None:
                    continue

                # Determine if the value is negative
                if current_value < 0:
                    weight_vector = weight_vector_neg
                else:
                    weight_vector = weight_vector_pos

                # Apply the weight
                weight = weight_vector[season_idx]
                weighted_sum += current_value * weight

            scores[col] = weighted_sum

        weighted_scores.append(scores)

    # Create the scores and rankings data frame
    scores_df = pd.DataFrame(weighted_scores)
    rankings_df = pd.concat([rankings_players.reset_index(drop=True), scores_df], axis=1)

    # Scale weighted scores per column
    scaled_scores_df = scores_df.copy()
    for col in score_cols:
        mask_valid = scores_df[col] != -999999
        if mask_valid.any():
            scaler = MinMaxScaler()
            scaled_vals = scaler.fit_transform(scores_df.loc[mask_valid, [col]])
            scaled_scores_df.loc[mask_valid, col] = scaled_vals.flatten()
        scaled_scores_df.loc[~mask_valid, col] = pd.NA

    # Add scaled scores to rankings_df
    for col in score_cols:
        rankings_df[col] = scaled_scores_df[col]

    # Rank player scores based on scaled values
    for col in score_cols:
        attr = col.split('_')[0]
        rankings_df[f'{attr}_rank'] = rankings_df[col].rank(ascending=False, method='dense', na_option='keep')

    # Save rankings CSV file
    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    filename = f'{season}_{position}_weighted_ranking.csv'
    file.save_csv(rankings_df, 'data_ranking', f'weighted_{pos_folder}', filename)
