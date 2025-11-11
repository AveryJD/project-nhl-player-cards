import requests
import pandas as pd
import time
import os
from utils import constants


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
