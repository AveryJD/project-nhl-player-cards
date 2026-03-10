# ====================================================================================================
# FUNCTIONS FOR LOADING AND SAVING DIFFERENT FILES
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image
import os
from utils import constants

DATA_DIR = constants.DATA_DIR
PROJECT_DIR = constants.PROJECT_DIR


def get_prev_season(cur_season: str) -> str:
    """
    Return the str for the previous season from a given season's str.

    :param cur_season: A str of the current season ('YYYY-YYYY')
    :return: A str of the season previous to the current season
    """
    start_year, end_year = map(int, cur_season.split("-"))
    prev_season = f"{start_year - 1}-{end_year - 1}"

    return prev_season

def get_next_season(cur_season: str) -> str:
    """
    Return the str for the next season from a given season's str.

    :param cur_season: A str of the current season ('YYYY-YYYY')
    :return: A str of the season previous to the current season
    """
    start_year, end_year = map(int, cur_season.split("-"))
    next_season = f"{start_year + 1}-{end_year + 1}"

    return next_season


def load_bios_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player bios CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the position ('F', 'D', or 'G')
    :return: The DataFrame containing the player bios
    """
    bio_file_name = f'{season}_{position}_bios.csv'
    bio_file_path = os.path.join(DATA_DIR, 'player_card_data', 'scraped_data', 'bios', bio_file_name)

    bios_df = pd.read_csv(bio_file_path)
    return bios_df


def load_salaries_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player salaries CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the position ('F', 'D', or 'G')
    :return: The DataFrame containing the player salaries
    """
    salaries_file_name = f'{season}_{position}_salaries.csv'
    salaries_file_path = os.path.join(DATA_DIR, 'player_card_data', 'scraped_data', 'salaries', salaries_file_name)

    bios_df = pd.read_csv(salaries_file_path)
    return bios_df


def load_stats_csv(season: str, position: str, situation: str) -> pd.DataFrame:
    """
    Load the player stats CSV for a given season, position, and situation.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param situation: A str representing the game situation ('all', '5v5', '5v4', or '4v5')
    :return: The DataFrame containing the player stats
    """
    stats_file_name = f'{season}_{position}_{situation}_stats.csv'
    stats_file_path = os.path.join(DATA_DIR, 'player_card_data', 'scraped_data', 'stats', stats_file_name)

    stats_df = pd.read_csv(stats_file_path)
    return stats_df


def load_rankings_csv(season: str, position: str, weighted: bool=True) -> pd.DataFrame:
    """
    Load the player rankings CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param pos: A str representing the player's position ('F', 'D', or 'G')
    :param weighted: A bool to check if the weightings to load are yearly or weighted
    :return: The DataFrame of the loaded rankings
    """
    if weighted:
        ranking_str = 'weighted'
    else:
        ranking_str = 'yearly'

    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'

    file_name = f'{season}_{position}_{ranking_str}_ranking.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'ranking_data', f'{ranking_str}_{pos_folder}', file_name)
    
    ranking_df = pd.read_csv(file_path)
    return ranking_df

def load_ids_csv(season: str) -> pd.DataFrame:
    """
    Load the player IDs CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the API information
    """
    ids_file_name = f'{season}_ids.csv'
    ids_file_path = os.path.join(DATA_DIR, 'player_card_data', 'scraped_data', 'ids', ids_file_name)

    ids_df = pd.read_csv(ids_file_path)
    return ids_df

def load_goalie_logs_csv(season: str) -> pd.DataFrame:
    """
    Load the goalie game logs CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the goalie game logs data
    """
    logs_file_name = f'{season}_goalie_logs.csv'
    logs_file_path = os.path.join(DATA_DIR, 'player_card_data', 'scraped_data', 'goalie_logs', logs_file_name)

    logs_df = pd.read_csv(logs_file_path)
    return logs_df


def load_card_data_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player card data CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: The DataFrame of the loaded card data
    """

    if position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'
    else:
        position = 'F'
        pos_folder = 'forwards'

    file_name = f'{season}_{position}_card_data.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'card_data', pos_folder, file_name)
    
    card_data_df = pd.read_csv(file_path)
    return card_data_df


def save_csv(df: pd.DataFrame, main_folder: str, sub_folder: str, file_name: str) -> None:
    """
    Save a DataFrame as a CSV file in a specified folder.

    :param df: The DataFrame to save
    :param main_folder: Main folder name name inside DATA_DIR
    :param sub_folder: Subfolder name inside the main folder
    :param file_name: Name of the CSV file to save
    :return: None
    """
    save_dir = os.path.join(DATA_DIR, 'player_card_data', main_folder, sub_folder)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file_name)

    df.to_csv(save_path, index=False)
    print(f"Saved {file_name}")


def save_card(card: Image, season: str, team: str, position: str, file_name: str) -> None:
    """
    Save a card PNG to a specified folder.

    :param card: The card image to save
    :param season: The season folder to save to
    :param team: The team folder inside the year folder to save to 
    :param position: The position folder inside the team folder to save to 
    :param file_name: Name of the card to save
    :return: None
    """
    save_dir = os.path.join(PROJECT_DIR, 'player_cards', season, team, position)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file_name)

    card.save(save_path, 'PNG')
    print(f"Saved {file_name}")