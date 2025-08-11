# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import rank_scores as rs
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR

skater_scorer = rs.SkaterScorer()
defensemen_scorer = rs.SkaterScorer()
goalie_scorer = rs.GoalieScorer()


def calculate_scores(position: str, season, all_row: pd.Series, evs_row: pd.Series, pkl_row: pd.Series, ppl_row: pd.Series=pd.Series()) -> dict:
    """
    ADD
    """
    if position != 'G':
        scores = {
            'evo_score': skater_scorer.offensive_score(evs_row, season),
            'evd_score': skater_scorer.defensive_score(evs_row, season),
            'ppl_score': skater_scorer.offensive_score(ppl_row, season),
            'pkl_score': skater_scorer.defensive_score(pkl_row, season),
            'oio_score': skater_scorer.oniceoffense_score(evs_row, season),
            'oid_score': skater_scorer.onicedefense_score(evs_row, season),
            'sht_score': skater_scorer.shooting_score(all_row, season),
            'scr_score': skater_scorer.scoring_score(all_row, season),
            'plm_score': skater_scorer.playmaking_score(all_row, season),
            'phy_score': skater_scorer.physicality_score(all_row, season),
            'pen_score': skater_scorer.penalties_score(all_row, season),
            'fof_score': skater_scorer.faceoff_score(all_row, season),
            'spd_score': 0,          # Might be used in the future
        }
    else:
        scores = {
            'all_score': goalie_scorer.total_score(all_row, season),
            'evs_score': goalie_scorer.total_score(evs_row, season),
            'pkl_score': goalie_scorer.total_score(pkl_row, season),
            'ldg_score': goalie_scorer.zone_score(all_row, season, 'LD'),
            'mdg_score': goalie_scorer.zone_score(all_row, season, 'MD'),
            'hdg_score': goalie_scorer.zone_score(all_row, season, 'HD'),
        }    

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
        ev_data = file.load_stats_csv(season, position, '5v5')
        pp_data = file.load_stats_csv(season, position, '5v4')
        pk_data = file.load_stats_csv(season, position, '4v5')

        # Filter skaters who do not meet the minimum games played requirement (25% of games played over the season)
        min_gp = constants.SEASON_GAMES[season] * 0.25
        valid_players = all_data.loc[all_data['GP'] >= min_gp, 'Player']

        all_data = all_data[all_data['Player'].isin(valid_players)]
        evs_data = ev_data[ev_data['Player'].isin(valid_players)]
        ppl_data = pp_data[pp_data['Player'].isin(valid_players)]
        pkl_data = pk_data[pk_data['Player'].isin(valid_players)]

        # Initialize ranking and scores lists
        rankings = all_data[['Player', 'Position', 'Team']].copy()
        scores_list = []

        # For each skater
        for _, all_row in all_data.iterrows():
            name = all_row['Player']
            pos = all_row['Position']

            # Get the skater's 5v5 data
            evs_row = evs_data.loc[evs_data['Player'] == name].iloc[0]

            # Get the skater's 5v4 data and filter based on TOI (30 seconds per game in the season requirement)
            if name in ppl_data['Player'].values:
                ppl_row = ppl_data.loc[ppl_data['Player'] == name].iloc[0]
                if ppl_row.get('TOI', 0) < constants.SEASON_GAMES[season] * 0.5:
                    ppl_row = pd.Series()
            else:
                ppl_row = pd.Series()

            # Get the skater's 4v5 data and filter based on TOI (30 seconds per game in the season requirement)
            if name in pkl_data['Player'].values:
                pkl_row = pkl_data.loc[pkl_data['Player'] == name].iloc[0]
                if pkl_row.get('TOI', 0) < constants.SEASON_GAMES[season] * 0.5:
                    pkl_row = pd.Series()
            else:
                pkl_row = pd.Series()

            # Faceoff threshold enforcement (3 faceoffs per game in the season requirement)
            total_fo = all_row.get('Faceoffs Won', 0) + all_row.get('Faceoffs Lost', 0)
            if total_fo < constants.SEASON_GAMES[season] * 3:
                all_row = all_row.copy()
                all_row['Faceoffs Won'] = 0
                all_row['Faceoffs Lost'] = 0

            # Calculate the skater's scores
            scores = calculate_scores(pos, all_row, evs_row, pkl_row, ppl_row)
            scores_list.append(scores)

        # Rank the skater's scores
        scores_df = pd.DataFrame(scores_list)
        rankings = pd.concat([pd.DataFrame({'Season': [season] * len(all_data)}), rankings.reset_index(drop=True), scores_df], axis=1)

    # For goalies
    else:
        # Load all goalie data
        all_data = file.load_stats_csv(season, 'G', 'all')
        ev_data = file.load_stats_csv(season, 'G', '5v5')
        pk_data = file.load_stats_csv(season, 'G', '4v5')

        # Filter goalies who do not meet the minimum games played requirement (15% of games played over the season)
        min_gp = constants.SEASON_GAMES[season] * 0.15
        valid_players = all_data.loc[all_data['GP'] >= min_gp, 'Player']

        all_data = all_data[all_data['Player'].isin(valid_players)]
        ev_data = ev_data[ev_data['Player'].isin(valid_players)]
        pk_data = pk_data[pk_data['Player'].isin(valid_players)]

        # Initialize ranking and scores lists
        rankings = all_data[['Player', 'Team']].copy()
        rankings.insert(1, 'Position', 'G')
        scores_list = []

        # For each goalie
        for _, row in all_data.iterrows():
            name = row['Player']

            # Get the goalie's's 5v5 and 4v5 data
            ev_row = ev_data.loc[ev_data['Player'] == name].iloc[0]
            pk_row = pk_data.loc[pk_data['Player'] == name].iloc[0]

            # Calculate the goalies's scores
            scores = calculate_scores('G', row, ev_row, pk_row, season)
            scores_list.append(scores)

        # Rank the goalies's scores
        scores_df = pd.DataFrame(scores_list)
        rankings = pd.concat([pd.DataFrame({'Season': [season] * len(all_data)}), rankings.reset_index(drop=True), scores_df], axis=1)


    # Correct column names
    score_columns = [col for col in scores_df.columns if col.endswith('_score')]
    for col in score_columns:
        attr = col.split('_')[0]
        rankings[f'{attr}_rank'] = rankings[col].rank(ascending=False, method='min')

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
        rankings[f'{attr}_rank'] = scores_for_rank.rank(ascending=False, method='min')

    # Save rankings CSV file
    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    filename = f'{season}_{position}_weighted_rankings.csv'
    file.save_csv(rankings, 'rankings', f'weighted_{pos_folder}', filename)
