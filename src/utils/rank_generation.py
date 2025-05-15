# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from utils import rank_scores as rs
from utils import constants

DATA_DIR = constants.DATA_DIR


def make_skater_rankings(season: str) -> None:
    
    # Read skater data
    all_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_all_skater_stats.csv')
    ev_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_ev_skater_stats.csv')
    pp_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_pp_skater_stats.csv')
    pk_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_pk_skater_stats.csv')

    # Filter out any skaters who haven't played over the minimum games played requirement
    min_gp_skaters = all_skater_data.loc[(all_skater_data['GP'] >= constants.MIN_GP_SKATER), 'Player']

    all_skater_data = all_skater_data[all_skater_data['Player'].isin(min_gp_skaters)]
    ev_skater_data = ev_skater_data[ev_skater_data['Player'].isin(min_gp_skaters)]
    pp_skater_data = pp_skater_data[pp_skater_data['Player'].isin(min_gp_skaters)]
    pk_skater_data = pk_skater_data[pk_skater_data['Player'].isin(min_gp_skaters)]

    # Start ranking DataFrame with the player names, positions, and teams
    s_rankings = all_skater_data[['Player', 'Position', 'Team']]

    # Make a list to store scores for all skaters
    scores_list = []

    # For every player in all player data, get their scores
    for _, all_row in all_skater_data.iterrows():
        player_name = all_row['Player']

        # Get rows from other dataframes
        ev_row = ev_skater_data[ev_skater_data['Player'] == player_name]
        pp_row = pp_skater_data[pp_skater_data['Player'] == player_name]
        pk_row = pk_skater_data[pk_skater_data['Player'] == player_name]

        # Get each situation row as a Series
        ev_row = ev_row.iloc[0]
        # Account for players who don't play special teams
        if not pp_row.empty:
            pp_row = pp_row.iloc[0] 
        else:
            pp_row = pd.Series()
        if not pk_row.empty:
            pk_row = pk_row.iloc[0] 
        else:
            pk_row = pd.Series()

        # MAKE OFF SCORE EVO + PPL
        # MAKE OFF SCORE EVD + PKL

        # Dictionary to store skater scores
        scores = {
            'off_score': rs.offensive_score(all_row),
            'def_score': rs.defensive_score(all_row),
            'evo_score': rs.offensive_score(ev_row),
            'evd_score': rs.defensive_score(ev_row),
            'ppl_score': rs.power_play_score(pp_row),
            'pkl_score': rs.penalty_kill_score(pk_row),
            'sht_score': rs.shooting_score(all_row),
            'plm_score': rs.playmaking_score(all_row),
            'phy_score': rs.physicality_score(all_row),
            'pen_score': rs.penalties_score(all_row),
            'fof_score': rs.faceoff_score(all_row),
            'spd_score': rs.speed_score(all_row)
        }

        # Append player scores to list
        scores_list.append(scores)

    # Convert the list of scores into a DataFrame
    scores_df = pd.DataFrame(scores_list)

    season_list = [season] * len(all_skater_data)
    season_df = pd.DataFrame(season_list, columns=['Season'])

    # Add scores to the skater rankings DataFrame
    s_rankings = pd.concat([season_df, s_rankings.reset_index(drop=True), scores_df], axis=1)

    # Separate forwards and defensemen rankings
    f_rankings = s_rankings[s_rankings['Position'] != 'D'][[
        'Season', 'Player', 'Position', 'Team',
        'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score',
        'sht_score', 'plm_score', 'phy_score', 'pen_score', 'fof_score', 'spd_score' 
    ]]

    d_rankings = s_rankings[s_rankings['Position'] == 'D'][[
        'Season', 'Player', 'Position', 'Team',
        'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score',
        'sht_score', 'plm_score', 'phy_score', 'pen_score', 'fof_score', 'spd_score'
    ]]

    # List of score columns to rank
    score_columns = [
        'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score',
        'sht_score', 'plm_score', 'phy_score', 'pen_score', 'fof_score', 'spd_score', 
    ]

    f_rankings = f_rankings.reset_index(drop=True)
    d_rankings = d_rankings.reset_index(drop=True)

    
    # Add ranking columns for forwards
    for column in score_columns:
        attribute, _ = column.split('_')
        f_rankings[f'{attribute}_rank'] = f_rankings[column].rank(ascending=False, method='min')

    # Add ranking columns for defensemen
    for column in score_columns:
        attribute, _ = column.split('_')
        d_rankings[f'{attribute}_rank'] = d_rankings[column].rank(ascending=False, method='min')

    # Save rankings to CSV
    f_rankings_path = f'{DATA_DIR}/data/player_rankings/forward_rankings/{season}_f_rankings.csv'
    d_rankings_path = f'{DATA_DIR}/data/player_rankings/defense_rankings/{season}_d_rankings.csv'

    f_rankings.to_csv(f_rankings_path, index=False)
    d_rankings.to_csv(d_rankings_path, index=False)

    print(f'{season} skater rankings created')



def make_goalie_rankings(season: str) -> None:

    all_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_all_goalie_stats.csv')
    ev_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_ev_goalie_stats.csv')
    pp_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_pp_goalie_stats.csv')
    pk_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_pk_goalie_stats.csv')

    # Filter out any goalies who haven't played over the minimum games played requirement
    min_gp_goalies = all_goalie_data.loc[(all_goalie_data['GP'] >= constants.MIN_GP_GOALIE), 'Player']

    all_goalie_data = all_goalie_data[all_goalie_data['Player'].isin(min_gp_goalies)]
    ev_goalie_data = ev_goalie_data[ev_goalie_data['Player'].isin(min_gp_goalies)]
    pp_goalie_data = pp_goalie_data[pp_goalie_data['Player'].isin(min_gp_goalies)]
    pk_goalie_data = pk_goalie_data[pk_goalie_data['Player'].isin(min_gp_goalies)]

    # Start ranking DataFrame with the goalie names, positions, and teams
    g_rankings = all_goalie_data[['Player', 'Team']]
    g_rankings.insert(1, 'Position', 'G')

    # Make a list to store scores for all goalies
    scores_list = []

    # For every goalie in all goalie data, get their scores
    for _, all_row in all_goalie_data.iterrows():

        goalie_name = all_row['Player']

        # Get rows from other situation dataframes
        ev_row = ev_goalie_data[ev_goalie_data['Player'] == goalie_name]
        pp_row = pp_goalie_data[pp_goalie_data['Player'] == goalie_name]
        pk_row = pk_goalie_data[pk_goalie_data['Player'] == goalie_name]

        # Get each situation row as a Series
        ev_row = ev_row.iloc[0]
        pp_row = pp_row.iloc[0]
        pk_row = pk_row.iloc[0]
        
        # Dictionary to store goalie scores
        scores = {
            'all_score': rs.goalie_all_score(all_row),
            'evs_score': rs.goalie_all_score(ev_row),
            'pkl_score': rs.goalie_all_score(pk_row),
            'ldg_score': rs.goalie_ldg_score(all_row),
            'mdg_score': rs.goalie_mdg_score(all_row),
            'hdg_score': rs.goalie_hdg_score(all_row),
        }

        # Append goalie scores to list
        scores_list.append(scores)

    # Convert the list of scores into a DataFrame
    scores_df = pd.DataFrame(scores_list)

    season_list = [season] * len(all_goalie_data)
    season_df = pd.DataFrame(season_list, columns=['Season'])

    # Add scores to the goalie rankings DataFrame
    g_rankings = pd.concat([season_df, g_rankings.reset_index(drop=True), scores_df], axis=1)


    # List of score columns to rank
    score_columns = [
        'all_score', 'evs_score', 'pkl_score',
        'ldg_score', 'mdg_score', 'hdg_score'
    ]

    g_rankings = g_rankings.reset_index(drop=True)
    
    # Add ranking columns for goalies
    for column in score_columns:
        attribute, _ = column.split('_')
        g_rankings[f'{attribute}_rank'] = g_rankings[column].rank(ascending=False, method='min')

    # Save ranking to CSV
    g_rankings_path = f'{DATA_DIR}/data/player_rankings/goalie_rankings/{season}_g_rankings.csv'
    g_rankings.to_csv(g_rankings_path, index=False)

    print(f'{season} goalie rankings created')
