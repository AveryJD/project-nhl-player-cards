import requests
import pandas as pd
import time
import os
from utils import constants
from utils import load_save as file


def get_player_ids(season: str) -> None:
    """
    Build a CSV of players with their NHL ID, team, and position from the NHL API

    :param season: A str of the season to get the data for ('YYYY-YYYY')
    :return: None
    """

    season_clean = season.replace('-', '')

    all_players = []

    for team in constants.TEAM_NAMES:
        url = f"https://api-web.nhle.com/v1/roster/{team}/{season_clean}"
        response = requests.get(url)
        if response.status_code != 200:
            continue

        roster = response.json()

        for pos in ['forwards', 'defensemen', 'goalies']:
            pos_code = {'forwards': 'F', 'defensemen': 'D', 'goalies': 'G'}[pos]

            for player in roster.get(pos, []):
                full_name = f"{player['firstName']['default']} {player['lastName']['default']}"
                pid = player['id']

                all_players.append({
                    'Player': full_name,
                    'Player ID': pid,
                    'Team': team,
                    'Position': pos_code,
                })

        time.sleep(0.10)

    ids_df = pd.DataFrame(all_players)
    ids_df = ids_df.sort_values(['Player', 'Position']).reset_index(drop=True)

    # Save IDs CSV
    os.makedirs('data_scraped/ids', exist_ok=True)
    filename = f'{season}_ids.csv'
    filepath = os.path.join('data_scraped/ids', filename)
    ids_df.to_csv(filepath, index=False)
    print(f"Saved {filename}")


def get_goalie_game_logs(season: str) -> None:
    """
    Retrieve game logs for all goalies for a given season, checking player IDs
    from the current, previous, and next seasons for comprehensive coverage.
    """

    season_clean = season.replace('-', '')
    
    # Get previous and next seasons
    prev_season = file.get_prev_season(season)
    next_season = file.get_next_season(season)

    # Helper to safely load IDs CSV
    def load_ids(s):
        path = os.path.join('data_scraped/ids', f'{s}_ids.csv')
        if os.path.exists(path):
            return pd.read_csv(path)
        return pd.DataFrame(columns=['Player', 'Player ID', 'Team', 'Position'])

    # Load IDs for current, previous, and next seasons
    ids_df_current = load_ids(season)
    ids_df_prev = load_ids(prev_season)
    ids_df_next = load_ids(next_season)

    # Combine all IDs from all three seasons
    all_ids = pd.concat([ids_df_current, ids_df_prev, ids_df_next], ignore_index=True)
    
    # Filter only goalies
    goalies_all = all_ids[all_ids['Position'] == 'G'].copy()
    
    # Group by Player ID
    goalie_fetch_data = goalies_all.groupby('Player ID').agg(
        # Get the player's name
        player_name=('Player', 'first'), 
    ).reset_index()

    all_logs = []

    # Loop over all unique Player IDs found across all three seasons.
    for _, row in goalie_fetch_data.iterrows():
        goalie_id = row['Player ID']
        player_name = row['player_name']
        
        # Check the single Player ID for game logs
        if pd.isna(goalie_id):
            continue
        
        # Get game logs for each player ID
        url = f"https://api-web.nhle.com/v1/player/{goalie_id}/game-log/{season_clean}/2"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            game_logs = data.get("gameLog", [])
            
            if game_logs:
                for g in game_logs:
                    all_logs.append({
                        'Player': player_name,
                        'Player ID': goalie_id, 
                        'Team': g.get('teamAbbrev'), 
                        'Game ID': g.get('gameId'),
                        'Date': g.get('gameDate'),
                        'Opponent': g.get('opponentAbbrev'),
                        'Home/Road': g.get('homeRoadFlag'),
                        'Result': g.get('decision'),
                        'Shots Against': g.get('shotsAgainst'),
                        'Goals Against': g.get('goalsAgainst'),
                        'Save %': g.get('savePctg'),
                        'Shutouts': g.get('shutouts'),
                        'TOI': g.get('toi'),
                    })
                
        # API delay after each ID check
        time.sleep(0.10)

    logs_df = pd.DataFrame(all_logs)
    logs_df = logs_df.sort_values(by=['Player', 'Player ID', 'Date']).reset_index(drop=True)

    # Save goalie game logs CSV
    os.makedirs('data_scraped/goalie_logs', exist_ok=True)
    filename = f'{season}_goalie_logs.csv'
    filepath = os.path.join('data_scraped/goalie_logs', filename)
    logs_df.to_csv(filepath, index=False)
    print(f"Saved {filename}")