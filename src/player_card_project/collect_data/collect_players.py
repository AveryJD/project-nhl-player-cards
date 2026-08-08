# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL PLAYER ID AND BIO DATA
# ====================================================================================================

# Imports
import requests
import pandas as pd
import time
from player_card_project import data_io
from player_card_project.collect_data import collect_utils


def scrape_player_ids(season: str) -> None:
    """
    Build a CSV of player IDs from the NHL API. Always a full rescrape -- overwrites any existing
    file for this season rather than merging into it.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """

    # Get all game IDs sorted with the most recently played game first
    game_ids = collect_utils.get_season_game_ids(season)
    game_ids = sorted(game_ids, reverse=True)

    position_group_map = {'forwards': 'F', 'defense': 'D', 'goalies': 'G'}

    seen_ids = set()
    all_players = []

    # Collect IDs from games in referse order (to preserve correct team player was on at the end of the season)
    for i, game_id in enumerate(game_ids):
        url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f'{season}: skipping game {game_id}, boxscore request returned {response.status_code}')
        else:
            boxscore = response.json()
            player_stats = boxscore.get('playerByGameStats', {})

            for side in ['awayTeam', 'homeTeam']:
                team_abbrev = boxscore.get(side, {}).get('abbrev')
                if team_abbrev is None:
                    continue

                side_stats = player_stats.get(side, {})

                for group, position_code in position_group_map.items():
                    for player in side_stats.get(group, []):
                        pid = player['playerId']

                        # Skip IDs that have already been found
                        if pid in seen_ids:
                            continue
                        seen_ids.add(pid)

                        # Get player full name
                        name_url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
                        name_response = requests.get(name_url, timeout=30)
                        name_data = name_response.json() if name_response.status_code == 200 else {}

                        first = name_data.get('firstName', {}).get('default', '')
                        last = name_data.get('lastName', {}).get('default', '')
                        full_name = f"{first} {last}".strip() or str(pid)

                        # Get player specific position
                        specific_position = player.get('position', position_code)

                        all_players.append({
                            'Player': full_name,
                            'Player ID': pid,
                            'Team': team_abbrev,
                            'Position': position_code,
                            'Specific Position': specific_position,
                        })

        # Progress print statement
        if (i + 1) % 100 == 0 or i == len(game_ids) - 1:
            print(f'{season}: processed {i + 1}/{len(game_ids)} games, {len(seen_ids)} player IDs found so far')

        # Brief delay to avoid hammering the NHL API
        time.sleep(0.10)

    player_ids_df = pd.DataFrame(all_players)
    player_ids_df = player_ids_df.sort_values(['Player', 'Position']).reset_index(drop=True)

    # Save IDs CSV
    file_name = f'{season}_player_ids.csv'
    data_io.save_csv(player_ids_df, 'raw_data', 'player_ids', file_name)


def scrape_bios(seasons: list) -> None:
    """
    Build a CSV of player bios from the NHL API.

    :param seasons: A list of str seasons ('YYYY-YYYY') to pull candidate Player IDs from
    :return: None
    """

    # Get all player IDs to get bios for
    all_ids = set()
    for season in seasons:

        player_ids_df = data_io.load_player_ids_csv(season)

        all_ids.update(int(pid) for pid in player_ids_df['Player ID'].dropna().unique())

    to_scrape = sorted(all_ids)

    new_rows = []
    # Collect player bios
    for i, player_id in enumerate(to_scrape):
        url = f'https://api-web.nhle.com/v1/player/{player_id}/landing'
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f'Skipping player {player_id}, bio request returned {response.status_code}')
            time.sleep(0.10)
            continue

        data = response.json()

        first_name = data.get('firstName')
        first = (first_name.get('default') if isinstance(first_name, dict) else first_name) or ''
        last_name = data.get('lastName')
        last = (last_name.get('default') if isinstance(last_name, dict) else last_name) or ''
        birth_city = data.get('birthCity')
        birth_city = birth_city.get('default') if isinstance(birth_city, dict) else birth_city
        birth_state_province = data.get('birthStateProvince')
        birth_state_province = birth_state_province.get('default') if isinstance(birth_state_province, dict) else birth_state_province

        draft = data.get('draftDetails') or {}

        new_rows.append({
            'Player ID': player_id,
            'Player': f'{first} {last}'.strip(),
            'Specific Position': data.get('position'),
            'Shoots Catches': data.get('shootsCatches'),
            'Height (in)': data.get('heightInInches'),
            'Height (cm)': data.get('heightInCentimeters'),
            'Weight (lb)': data.get('weightInPounds'),
            'Weight (kg)': data.get('weightInKilograms'),
            'Birth Date': data.get('birthDate'),
            'Birth City': birth_city,
            'Birth State Province': birth_state_province,
            'Birth Country': data.get('birthCountry'),
            'Draft Year': draft.get('year'),
            'Draft Round': draft.get('round'),
            'Draft Overall Pick': draft.get('overallPick'),
            'Draft Team': draft.get('teamAbbrev'),
        })

        # Progress print statement
        if (i + 1) % 100 == 0 or i == len(to_scrape) - 1:
            print(f'Processed {i + 1}/{len(to_scrape)} player bios')

        # Brief delay to avoid hammering the NHL API
        time.sleep(0.10)

    bios_df = pd.DataFrame(new_rows)
    bios_df = bios_df.sort_values('Player ID').reset_index(drop=True)

    # Save bios CSV -- full overwrite, no merge with whatever was already saved
    data_io.save_csv(bios_df, 'raw_data', 'player_bios', 'player_bios.csv')
