# ====================================================================================================
# GENERAL HELPER FUNCTIONS SHARED ACROSS COLLECT DATA'S SCRAPE MODULES
# ====================================================================================================

# Imports
import requests
import pandas as pd
import time
import os
import warnings
from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR


def get_season_game_ids(season: str) -> list:
    """
    Get every unique game ID played in a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A sorted list of unique int game IDs
    """
    season_clean = season.replace('-', '')
    game_ids = set()

    # Get every game from every team
    for team in constants.TEAM_NAMES:
        url = f'https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_clean}'
        response = requests.get(url, timeout=30)

        games = response.json().get('games', [])
        regular_season_gametype = 2
        for game in games:
            if game.get('gameType') == regular_season_gametype and game.get('gameState') in ('FINAL', 'OFF'):
                game_ids.add(game['id'])

        # Brief delay to avoid hammering the NHL API
        time.sleep(0.10)

    sorted_game_ids = sorted(game_ids)
    return sorted_game_ids


def get_game_play_by_play(game_id: int) -> dict:
    """
    Fetch a single game's play-by-play (faceoffs/goals/shot/penalty/possession events) JSON

    :param game_id: The NHL game ID to fetch play-by-play for
    :return: The play-by-play JSON as a dict
    """
    url = f'https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play'
    response = requests.get(url, timeout=30)
    pbp_data = response.json()
    return pbp_data


def team_id_to_abbrev_map(data: dict) -> dict:
    """
    Build a team ID to abbreviation map.

    :param data: A play-by-play dict
    :return: A team_id to abbreviation dict
    """
    team_id_to_abbrev = {}
    for side in ('awayTeam', 'homeTeam'):
        team = data.get(side, {})
        if 'id' in team and 'abbrev' in team:
            team_id_to_abbrev[team['id']] = team['abbrev']
    return team_id_to_abbrev


def scrape_generic(
    ids: list,
    fetch_fn,
    outputs: list,
    no_data_folder: str,
    no_data_file_name: str,
    label: str,
    id_column: str,
) -> None:
    """
    Shared resume/no-data-tracking/checkpoint/rate-limit scraping loop used by every scrape function.

    :param ids: A list of IDs (e.g. game IDs or player IDs) to fetch data for
    :param fetch_fn: A callable taking a single ID and returning a DataFrame or tuple of DataFrames matching `outputs`
    :param outputs: A list of (folder, file_name) tuples, one per DataFrame fetch_fn returns
    :param no_data_folder: The raw_data subfolder for this scrape's no-data CSV
    :param no_data_file_name: The no-data CSV's file name
    :param label: A short str describing this scrape, used in progress print messages
    :param id_column: The column name identifying each row's ID in the outputs/no-data CSVs
    :return: None
    """
    no_data_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', no_data_folder, no_data_file_name)

    existing_dfs = []
    for folder, file_name in outputs:
        path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', folder, file_name)
        existing_dfs.append(pd.read_csv(path) if os.path.exists(path) else pd.DataFrame())

    done_ids = set(existing_dfs[0][id_column].unique()) if not existing_dfs[0].empty else set()

    if os.path.exists(no_data_path):
        no_data_ids = set(pd.read_csv(no_data_path)[id_column].unique())
    else:
        no_data_ids = set()

    remaining_ids = [i for i in ids if i not in done_ids and i not in no_data_ids]

    new_chunks = [[] for _ in outputs]
    new_no_data_ids = []
    for i, entity_id in enumerate(remaining_ids):
        result = fetch_fn(entity_id)

        results = result if isinstance(result, tuple) else (result,)

        if any(not df.empty for df in results):
            for chunks, df in zip(new_chunks, results):
                chunks.append(df)
        else:
            new_no_data_ids.append(entity_id)

        # Save progress periodically so a long scrape can be interrupted safely
        if (i + 1) % 100 == 0 or i == len(remaining_ids) - 1:
            for idx, (folder, file_name) in enumerate(outputs):
                if new_chunks[idx]:
                    to_concat = [df for df in [existing_dfs[idx]] + new_chunks[idx] if not df.empty]
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', FutureWarning)
                        combined_df = pd.concat(to_concat, ignore_index=True)
                    data_io.save_csv(combined_df, 'raw_data', folder, file_name)
                    existing_dfs[idx] = combined_df
                    new_chunks[idx] = []
            if new_no_data_ids:
                no_data_ids.update(new_no_data_ids)
                no_data_df = pd.DataFrame({id_column: sorted(no_data_ids)})
                data_io.save_csv(no_data_df, 'raw_data', no_data_folder, no_data_file_name)
                new_no_data_ids = []
            # Progress print statement
            print(f'{label}: processed {i + 1}/{len(remaining_ids)} remaining')

        # Brief delay to avoid hammering the NHL API
        time.sleep(0.10)
