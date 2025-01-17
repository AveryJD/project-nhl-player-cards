
import pandas as pd

DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'
SEASON = '2023-2024'

### Player stats from MoneyPuck: https://moneypuck.com/data.htm
all_player_data = pd.read_csv(f'{DATA_DIR}/NHL Player Data/{SEASON}_skaters.csv')

# Filter out any players who haven't played over 100 minutes in all situations
min_toi = 100

min_toi_players = all_player_data.loc[
    (all_player_data['situation'] == 'all') & 
    (all_player_data['icetime'] >= min_toi * 60),
    'playerId' ]

filtered_data = all_player_data[all_player_data['playerId'].isin(min_toi_players)]

# Sort data by position
f_player_data = filtered_data[
    (filtered_data['position'] == 'C') | 
    (filtered_data['position'] == 'L') | 
    (filtered_data['position'] == 'R') ]
c_player_data = filtered_data[filtered_data['position'] == 'C']
lw_player_data = filtered_data[filtered_data['position'] == 'L']
rw_player_data = filtered_data[filtered_data['position'] == 'R']
d_player_data = filtered_data[filtered_data['position'] == 'D']

