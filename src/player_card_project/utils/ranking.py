# ====================================================================================================
# FUNCTIONS FOR RANKING PLAYER ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from player_card_project.utils import scoring
from player_card_project.utils import constants
from player_card_project.utils import load_save as file



def attach_percentiles(rankings: pd.DataFrame, score_columns: list) -> None:
    """
    Attach a percentile and rank column per score column, plus total qualifying player counts for different strength situations.

    :param rankings: The rankings DataFrame to add columns to
    :param score_columns: The score columns to convert
    :return: None
    """
    for col in score_columns:
        attr = col[:-len('_score')]
        pct_col = f'{attr}_pct'
        rank_col = f'{attr}_rank'
        rankings[pct_col] = (rankings[col].rank(pct=True, na_option='keep') * 100).round(1).astype('Float64')
        rankings[rank_col] = rankings[col].rank(method='dense', ascending=False, na_option='keep').astype('Int64')

    rankings['all_players'] = len(rankings)
    if 'ppl_score' in rankings.columns:
        rankings['ppl_players'] = int(rankings['ppl_score'].notna().sum())
    if 'pkl_score' in rankings.columns:
        rankings['pkl_players'] = int(rankings['pkl_score'].notna().sum())


def calculate_scores(season: str, position: str, all_df: pd.DataFrame, evs_df: pd.DataFrame, pkl_df: pd.DataFrame, ppl_df: pd.DataFrame = None, goalie_logs_df=None) -> pd.DataFrame:
    """
    Calculate player scores for all attributes.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param all_df: A DataFrame containing the players stats from all situations
    :param evs_df: A DataFrame containing the players 5v5 stats
    :param pkl_df: A DataFrame containing the players 4v5 stats
    :param ppl_df: A DataFrame containing the players 5v4 stats (default is None to account for goalies)
    :param goalie_logs_df: A DataFrame containing the goalies game logs (default is None to account for skaters)
    :return: A DataFrame of scores
    """

    skater_scorer = scoring.SkaterScorer(position, season) if position != 'G' else None
    goalie_scorer = scoring.GoalieScorer(season) if position == 'G' else None

    # Calculate skater scores
    if position != 'G':
        scores = pd.DataFrame({
            'ovr_score': skater_scorer.total_war_score(all_df),
            'evo_score': skater_scorer.offensive_war_score(evs_df),
            'evd_score': skater_scorer.defensive_war_score(evs_df),
            'ppl_score': skater_scorer.offensive_war_score(ppl_df, is_ppl=True),
            'pkl_score': skater_scorer.defensive_war_score(pkl_df, is_pkl=True),
            'fin_score': skater_scorer.finishing_war_score(all_df),
            'pen_score': skater_scorer.penalty_war_score(all_df),
            'xgl_score': skater_scorer.secondary_score(evs_df, 'ixG'),
            'gol_score': skater_scorer.secondary_score(evs_df, 'Goals'),
            'ast_score': skater_scorer.secondary_score(evs_df, 'Assists'),
            'hit_score': skater_scorer.secondary_score(evs_df, 'Physicality'),
            'ozs_score': skater_scorer.secondary_score(evs_df, 'O-Zone Starts', total=True),
            'pdo_score': skater_scorer.secondary_score(evs_df, 'PDO', total=True),
        }, index=all_df.index)

    # Calculate goalie scores
    else:
        scores = pd.DataFrame({
            'ovr_score': goalie_scorer.total_war_score(all_df),
            'evs_score': goalie_scorer.evs_war_score(evs_df),
            'pkl_score': goalie_scorer.pkl_war_score(pkl_df),
            'ldg_score': goalie_scorer.zone_score(evs_df, 'LD'),
            'mdg_score': goalie_scorer.zone_score(evs_df, 'MD'),
            'hdg_score': goalie_scorer.zone_score(evs_df, 'HD'),
            'rbd_score': goalie_scorer.rebound_score(evs_df),
            'tmd_score': goalie_scorer.team_d_score(evs_df),
            'gre_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Great'),
            'qal_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Quality'),
            'bad_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Bad'),
            'awf_score': goalie_scorer.start_score(all_df, goalie_logs_df, 'Awful'),
            'wrk_score': goalie_scorer.workload_score(all_df),
        }, index=all_df.index)

    return scores


def make_skater_scores(season: str, position: str) -> pd.DataFrame:
    """
    Load stats and compute raw skater scores for a single season/position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F' or 'D')
    :return: A DataFrame with raw scores
    """
    # Load all skater data
    all_data = file.load_stats_csv(season, position, 'all')
    evs_data = file.load_stats_csv(season, position, '5v5')
    ppl_data = file.load_stats_csv(season, position, '5v4')
    pkl_data = file.load_stats_csv(season, position, '4v5')

    all_data = all_data.set_index('Player ID')
    evs_data = evs_data.set_index('Player ID')
    ppl_data = ppl_data.set_index('Player ID')
    pkl_data = pkl_data.set_index('Player ID')

    # Filter skaters who do not meet the minimum games played requirement
    min_toi = constants.SEASON_GAMES[season] * constants.SKATER_MIN_TOI
    valid_players = all_data.loc[all_data['TOI'] >= min_toi].index
    all_data = all_data.loc[valid_players]

    # Ensure all DataFrames share the same index
    common_index = all_data.index
    evs_data = evs_data.reindex(common_index).fillna(0)
    ppl_data = ppl_data.reindex(common_index).fillna(0)
    pkl_data = pkl_data.reindex(common_index).fillna(0)

    # Filter skaters who meet the minimum special teams TOI requirement
    min_power_play = constants.SKATER_MIN_PP
    min_penalty_kill = constants.SKATER_MIN_PK
    valid_ppl_players = ppl_data.loc[ppl_data['TOI'] >= all_data['GP'] * min_power_play].index
    valid_pkl_players = pkl_data.loc[pkl_data['TOI'] >= all_data['GP'] * min_penalty_kill].index

    # Boolean masks of invalid player scores
    invalid_ppl = ~ppl_data.index.isin(valid_ppl_players)
    invalid_pkl = ~pkl_data.index.isin(valid_pkl_players)

    # Calculate skater scores
    scores_df = calculate_scores(season, position, all_data, evs_data, pkl_data, ppl_df=ppl_data)

    # Mask invalid PP/PK players' scores
    scores_df.loc[invalid_ppl, 'ppl_score'] = pd.NA
    scores_df.loc[invalid_pkl, 'pkl_score'] = pd.NA

    # Carry Player/Team through for display -- calculate_scores only returns score columns
    scores_df = all_data[['Player', 'Team']].join(scores_df)

    return scores_df


def make_goalie_scores(season: str) -> pd.DataFrame:
    """
    Load stats and compute raw skater scores for a single season/position.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A DataFrame with raw scores
    """

    # Load all goalie data
    all_data = file.load_stats_csv(season, 'G', 'all')
    evs_data = file.load_stats_csv(season, 'G', '5v5')
    pkl_data = file.load_stats_csv(season, 'G', '4v5')
    logs_data = file.load_goalie_logs_csv(season)

    # Indexed by Player ID
    all_data = all_data.set_index('Player ID')
    evs_data = evs_data.set_index('Player ID')
    pkl_data = pkl_data.set_index('Player ID')

    # Filter goalies who do not meet the minimum games played requirement (15% of games played over the season)
    min_games = constants.SEASON_GAMES[season] * constants.GOALIE_MIN_GP
    valid_players = all_data.loc[all_data['GP'] >= min_games].index

    all_data = all_data.loc[valid_players]
    evs_data = evs_data.loc[valid_players]
    pkl_data = pkl_data.loc[valid_players]

    # Calculate goalie scores -- logs_data is left keyed by its own 'Player ID' column
    # (GoalieScorer.start_score merges on it directly)
    scores_df = calculate_scores(season, 'G', all_data, evs_data, pkl_data, goalie_logs_df=logs_data)

    # Carry Player/Team through for display -- calculate_scores only returns score columns
    scores_df = all_data[['Player', 'Team']].join(scores_df)

    return scores_df


def make_player_rankings(season: str, position: str) -> None:
    """
    Generate player rankings for a specific season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: None
    """

    # Make skater scores
    if position != 'G':
        # Get skater scores
        scores_df = make_skater_scores(season, position)

        # Calculate a combined forward and defenseman score pool for quality of teammates and competition
        if position == 'F':
            other_position = 'D'
        else:
            other_position = 'F'
        other_scores_df = make_skater_scores(season, other_position)
        combined_scores = pd.concat([scores_df, other_scores_df])

        # Get offense quality and defense quality
        es_offense_quality = scoring.compute_quality_metrics(season, combined_scores, situation='ES', talent_col='evo_score')
        es_defense_quality = scoring.compute_quality_metrics(season, combined_scores, situation='ES', talent_col='evd_score')

        # Get teammates and competition scores
        general_es_quality = scoring.average_quality_metrics(es_offense_quality, es_defense_quality)
        scores_with_es_display = scoring.attach_quality_to_scores(scores_df, general_es_quality)
        scores_df['tmt_score'] = scores_with_es_display['qot_score']
        scores_df['cmp_score'] = scores_with_es_display['qoc_score']

        # Put together scores DataFrame
        rankings = scores_df.reset_index()
        rankings.insert(3, 'Position', position)
        rankings.insert(0, 'Season', season)

    # Make goalie scores
    else:
        # Get goalie scores
        scores_df = make_goalie_scores(season)

        # Put together scores DataFrame
        rankings = scores_df.reset_index()
        rankings.insert(3, 'Position', position)
        rankings.insert(0, 'Season', season)

    # Convert every raw score into a percentile and ranking
    score_columns = [col for col in scores_df.columns if col.endswith('_score')]
    attach_percentiles(rankings, score_columns)

    # Save rankings CSV file
    pos_folder = constants.POSITION_FOLDERS[position]
    filename = f'{season}_{position}_yearly_ranking.csv'
    file.save_csv(rankings, 'ranking_data', f'yearly_{pos_folder}', filename)


def make_player_weighted_rankings(season: str, position: str) -> None:
    """
    Generate weighted player rankings for a specific season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: None
    """

    # Load current season rankings
    cur_rankings = file.load_rankings_csv(season, position, weighted=False)

    # Check if previous seasons are available
    prev_season = file.get_prev_season(season)
    if prev_season not in constants.DATA_SEASONS:
        prev_season = None

    if prev_season is not None:
        prev_prev_season = file.get_prev_season(prev_season)
        if prev_prev_season not in constants.DATA_SEASONS:
            prev_prev_season = None
    else:
        prev_prev_season = None

    # Load previous rankings if available
    if prev_season is not None:
        prev_rankings = file.load_rankings_csv(prev_season, position, weighted=False)
    else:
        prev_rankings = pd.DataFrame()

    if prev_prev_season is not None:
        prev_prev_rankings = file.load_rankings_csv(prev_prev_season, position, weighted=False)
    else:
        prev_prev_rankings = pd.DataFrame()

    # Determine players to rank (those in the current season)
    rankings_players = cur_rankings[['Season', 'Player ID', 'Player', 'Position', 'Team']].copy()

    # Determine the score columns
    score_cols = []
    for column in cur_rankings.columns:
        if column.endswith('_score'):
            score_cols.append(column)

    # Initialized list to store weighted scores
    weighted_scores = []

    # For each player calculate their weighted scores
    for _, row in rankings_players.iterrows():
        player_id = row['Player ID']
        scores = {}

        # Get the scores from each season, matched by Player ID
        if not prev_prev_rankings.empty:
            row_prev_prev = prev_prev_rankings[prev_prev_rankings['Player ID'] == player_id]
        else:
            row_prev_prev = pd.DataFrame()

        if not prev_rankings.empty:
            row_prev = prev_rankings[prev_rankings['Player ID'] == player_id]
        else:
            row_prev = pd.DataFrame()
            row_prev_prev = pd.DataFrame()

        if not cur_rankings.empty:
            row_cur = cur_rankings[cur_rankings['Player ID'] == player_id]
        else:
            row_cur = pd.DataFrame()
            row_prev = pd.DataFrame()
            row_prev_prev = pd.DataFrame()

        season_rows = [row_cur, row_prev, row_prev_prev]

        # Calculate weighted scores for each score column
        for col in score_cols:

            # Get score values
            values = []
            for df in season_rows:
                if not df.empty:
                    value = df.iloc[0][col]
                    values.append(None if pd.isna(value) else value)
                else:
                    values.append(None)

            # If the player doesn't have scores for the current season, skip them
            if values[0] is None:
                scores[col] = pd.NA
                continue

            # Count valid seasons
            num_valid = sum(value is not None for value in values)

            # Select the proper weight vectors
            if position != 'G':
                if num_valid == 3:
                    weight_vector = constants.SKATER_THREE_SEASONS_WEIGHTS
                elif num_valid == 2:
                    if values[1] is not None:
                        weight_vector = constants.SKATER_TWO_SEASONS_WEIGHTS
                    else:
                        weight_vector = constants.SKATER_TWO_SEASONS_WEIGHTS_GAP
                elif num_valid == 1:
                    weight_vector = constants.SKATER_ONE_SEASON_WEIGHTS

            else:
                if num_valid == 3:
                    weight_vector = constants.GOALIE_THREE_SEASONS_WEIGHTS
                elif num_valid == 2:
                    if values[1] is not None:
                        weight_vector = constants.GOALIE_TWO_SEASONS_WEIGHTS
                    else:
                        weight_vector = constants.GOALIE_TWO_SEASONS_WEIGHTS_GAP
                elif num_valid == 1:
                    weight_vector = constants.GOALIE_ONE_SEASON_WEIGHTS

            # Calculate weighted score
            weighted_sum = 0

            for season_idx, current_value in enumerate(values):
                if current_value is None:
                    continue

                # Apply the weight
                weight = weight_vector[season_idx]
                weighted_sum += current_value * weight

            scores[col] = weighted_sum

        weighted_scores.append(scores)

    # Put together weighted rankings DataFrame
    scores_df = pd.DataFrame(weighted_scores)
    rankings_df = pd.concat([rankings_players.reset_index(drop=True), scores_df], axis=1)

    # Convert every weighted score into a percentile against this season's qualifying pool
    attach_percentiles(rankings_df, score_cols)

    # Save rankings CSV file
    pos_folder = constants.POSITION_FOLDERS[position]
    filename = f'{season}_{position}_weighted_ranking.csv'
    file.save_csv(rankings_df, 'ranking_data', f'weighted_{pos_folder}', filename)
