# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
import os
from utils import rank_scores as rs
from utils import constants

DATA_DIR = constants.DATA_DIR


def make_skater_rankings(season: str) -> None:
    
    # Read skater data
    all_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_skater_all_stats.csv')
    ev_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_skater_ev_stats.csv')
    pp_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_skater_pp_stats.csv')
    pk_skater_data = pd.read_csv(f'{DATA_DIR}/data/player_data/skater_stats/{season}_skater_pk_stats.csv')

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
        player_position = all_row['Position']


        # Get skater row dataframes from other dataframes (Use name and position to avoid players with the same name having stats combined)
        ev_df = ev_skater_data[
            (ev_skater_data['Player'] == player_name) &
            (ev_skater_data['Position'] == player_position)]
        pp_df = pp_skater_data[
            (pp_skater_data['Player'] == player_name) &
            (pp_skater_data['Position'] == player_position)]
        pk_df = pk_skater_data[
            (pk_skater_data['Player'] == player_name) &
            (pk_skater_data['Position'] == player_position)]


        # Get each situation row as a Series (account for players who don't play special teams)
        ev_row = ev_df.iloc[0]
        if not pp_df.empty:
            pp_row = pp_df.iloc[0] 

            off_df = pd.concat([ev_df, pp_df], ignore_index=True)
            off_df = off_df.apply(pd.to_numeric, errors='coerce')
            off_row = off_df.sum(axis=0)
        else:
            pp_row = pd.Series()
            off_row = ev_row.copy()

        if not pk_df.empty:
            pk_row = pk_df.iloc[0] 

            def_df = pd.concat([ev_df, pk_df], ignore_index=True)
            def_df = def_df.apply(pd.to_numeric, errors='coerce')
            def_row = def_df.sum(axis=0)
        else:
            pk_row = pd.Series()
            def_row = ev_row.copy()

        # Dictionary to store skater scores
        scores = {
            'off_score': rs.offensive_score(off_row),
            'def_score': rs.defensive_score(def_row),
            'evo_score': rs.offensive_score(ev_row),
            'evd_score': rs.defensive_score(ev_row),
            'ppl_score': rs.power_play_score(pp_row),
            'pkl_score': rs.penalty_kill_score(pk_row),
            'sht_score': rs.shooting_score(off_row),
            'plm_score': rs.playmaking_score(off_row),
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

    # Save forward rankings as a CSV in the proper location
    f_save_dir = os.path.join(DATA_DIR, 'data', 'player_rankings', 'forward_rankings')
    os.makedirs(f_save_dir, exist_ok=True)
    f_save_path = os.path.join(f_save_dir, f'{season}_f_rankings.csv')
    f_rankings.to_csv(f_save_path, index=False)

    # Save defense rankings as a CSV in the proper location
    d_save_dir = os.path.join(DATA_DIR, 'data', 'player_rankings', 'defense_rankings')
    os.makedirs(d_save_dir, exist_ok=True)
    d_save_path = os.path.join(d_save_dir, f'{season}_d_rankings.csv')
    d_rankings.to_csv(d_save_path, index=False)

    print(f"{season} skater rankings created")



def make_goalie_rankings(season: str) -> None:

    all_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_goalie_all_stats.csv')
    ev_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_goalie_ev_stats.csv')
    pk_goalie_data = pd.read_csv(f'{DATA_DIR}/data/player_data/goalie_stats/{season}_goalie_pk_stats.csv')

    # Filter out any goalies who haven't played over the minimum games played requirement
    min_gp_goalies = all_goalie_data.loc[(all_goalie_data['GP'] >= constants.MIN_GP_GOALIE), 'Player']

    all_goalie_data = all_goalie_data[all_goalie_data['Player'].isin(min_gp_goalies)]
    ev_goalie_data = ev_goalie_data[ev_goalie_data['Player'].isin(min_gp_goalies)]
    pk_goalie_data = pk_goalie_data[pk_goalie_data['Player'].isin(min_gp_goalies)]

    # Start ranking DataFrame with the goalie names, positions, and teams
    g_rankings = all_goalie_data[['Player', 'Team']]
    g_rankings.insert(1, 'Position', 'G')

    # Make a list to store scores for all goalies
    scores_list = []

    # For every goalie in all goalie data, get their scores
    for _, all_row in all_goalie_data.iterrows():

        goalie_name = all_row['Player']

        # Get goalie row dataframes from other dataframes
        ev_df = ev_goalie_data[ev_goalie_data['Player'] == goalie_name]
        pk_df = pk_goalie_data[pk_goalie_data['Player'] == goalie_name]

        # Get each situation row as a Series
        ev_row = ev_df.iloc[0]
        pk_row = pk_df.iloc[0]
        
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

    # Save goalie rankings as a CSV in the proper location
    g_save_dir = os.path.join(DATA_DIR, 'data', 'player_rankings', 'goalie_rankings')
    os.makedirs(g_save_dir, exist_ok=True)
    g_save_path = os.path.join(g_save_dir, f'{season}_g_rankings.csv')
    g_rankings.to_csv(g_save_path, index=False)

    print(f'{season} goalie rankings created')
