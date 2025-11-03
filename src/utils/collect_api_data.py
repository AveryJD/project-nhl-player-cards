import requests
import pandas as pd
import time
import os
from utils import constants


def build_season_player_csv(season: str):
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

    df_season = pd.DataFrame(all_players)
    df_season = df_season.sort_values(['Player', 'Position']).reset_index(drop=True)

    # Save API CSV
    os.makedirs('data_scraped/api', exist_ok=True)
    filename = f'{season}_api.csv'
    filepath = os.path.join('data_scraped/api', filename)
    df_season.to_csv(filepath, index=False)
    print(f"Saved {filename}")
