
import pandas as pd

import player_rankings as pr

DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'

# The two years of the season
SEASON = '2022-2023'
# The teams of a season
TEAMS = [
    'ANA', 'ARI', 'BOS', 'BUF', 'CGY', 'CAR', 'CHI', 'COL', 'CBJ', 'DAL', 
    'DET', 'EDM', 'FLA', 'LAK', 'MIN', 'MTL', 'NSH', 'NJD', 'NYI', 'NYR', 
    'OTT', 'PHI', 'PIT', 'SEA', 'SJS', 'STL', 'TBL', 'TOR', 'VAN', 'VGK', 
    'WSH', 'WPG'
]   # 'ARI' for 2023-2024 and before; 'UTA' for 2024-2025 and after


### Player stats from MoneyPuck: https://moneypuck.com/data.htm
all_player_data = pd.read_csv(f'{DATA_DIR}/NHL Player Data/{SEASON}_skaters.csv')

# Filter out any players who haven't played over 100 minutes in all situations
min_toi = 100

min_toi_players = all_player_data.loc[
    (all_player_data['situation'] == 'all') & 
    (all_player_data['icetime'] >= min_toi * 60),
    'playerId' ]

player_data = all_player_data[all_player_data['playerId'].isin(min_toi_players)]


# Initialize a list to store scores for all players
scores_list = []

# Loop through each player in the player_data DataFrame
for index, row in player_data.iterrows():
    # Dictionary to store scores for the current player
    scores = {
        'off_score': 0,
        'def_score': 0,
        'sht_score': 0,
        'plm_score': 0,
        'phy_score': 0,
        'spd_score': 0,
        'evo_score': 0,
        'evd_score': 0,
        'ppl_score': 0,
        'pkl_score': 0
    }

    # Calculate scores for the current player
    if row['situation'] == 'all':
        scores['off_score'] = pr.offensive_score(row)
        scores['def_score'] = pr.defensive_score(row)
        scores['sht_score'] = pr.shooting_score(row)
        scores['plm_score'] = pr.playmaking_score(row)
        scores['phy_score'] = pr.physicality_score(row)
        scores['spd_score'] = pr.speed_score(row)
    elif row['situation'] == '5on5':
        scores['evo_score'] = pr.offensive_score(row)
        scores['evd_score'] = pr.defensive_score(row)
    elif row['situation'] == '5on4':
        scores['ppl_score'] = pr.power_play_score(row)
    elif row['situation'] == '4on5':
        scores['pkl_score'] = pr.penalty_kill_score(row)

    # Append the calculated scores to the all_scores list
    scores_list.append(scores)

# Convert the list of scores into a DataFrame
scores_df = pd.DataFrame(scores_list)

# Combine scores_df with player_data
player_data = pd.concat([player_data.reset_index(drop=True), scores_df], axis=1)

# Add a 'season' column to player_data
player_data['season'] = SEASON

# Group player scores to one row
    ['season', 'name', 'team', 'position'],
    as_index=False
).agg({
    'off_score': 'sum',
    'def_score': 'sum',
    'evo_score': 'sum',
    'evd_score': 'sum',
    'ppl_score': 'sum',
    'pkl_score': 'sum',
    'sht_score': 'sum',
    'plm_score': 'sum',
    'phy_score': 'sum',
    'spd_score': 'sum'
})

# Separate forwards and defensemen rankings
f_rankings_df = player_data[player_data['position'].isin(['C', 'L', 'R'])][[
    'season', 'name', 'team', 'position', 
    'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score',
    'sht_score', 'plm_score', 'phy_score', 'spd_score', 
]]

d_rankings_df = player_data[player_data['position'] == 'D'][[
    'season', 'name', 'team', 'position', 
    'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score',
    'sht_score', 'plm_score', 'phy_score', 'spd_score', 
]]

# List of score columns to rank
score_columns = [
    'off_score', 'def_score', 'evo_score', 'evd_score', 'ppl_score', 'pkl_score', 
    'sht_score', 'plm_score', 'phy_score', 'spd_score'
]

# Add ranking columns for forwards
for column in score_columns:
    f_rankings_df[f'{column}_rank'] = f_rankings_df[column].rank(ascending=False, method='min')

# Add ranking columns for defensemen
for column in score_columns:
    d_rankings_df[f'{column}_rank'] = d_rankings_df[column].rank(ascending=False, method='min')

# Save rankings to CSV
f_rankings_df.to_csv(f'{DATA_DIR}/NHL Player Data/f_rankings_{SEASON}.csv', index=False)
d_rankings_df.to_csv(f'{DATA_DIR}/NHL Player Data/d_rankings_{SEASON}.csv', index=False)


