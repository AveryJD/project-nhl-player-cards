# ====================================================================================================
# FUNCTIONS FOR LOADING AND SAVING DIFFERENT FILES
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image
import os
from utils import constants

DATA_DIR = constants.DATA_DIR


def get_prev_season(cur_season: str) -> str:
    """
    Return the str for previous season from a given season's str.

    :param cur_season: a str of the current season ('YYYY-YYYY')
    :return: a str of the season previous to the current season
    """
    start_year, end_year = map(int, cur_season.split("-"))
    prev_season = f"{start_year - 1}-{end_year - 1}"

    return prev_season


def load_bios_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player bios CSV for a given season and position.

    :param season: a str representing the season ('YYYY-YYYY')
    :param position: a str representing the position ('F', 'D', or 'G')
    :return: DataFrame containing the player bios
    """
    bio_filename = f'{season}_{position}_bios.csv'
    bio_file_path = os.path.join(DATA_DIR, 'data', 'bios', bio_filename)

    bios_df = pd.read_csv(bio_file_path)
    return bios_df


def load_stats_csv(season: str, position: str, situation: str) -> pd.DataFrame:
    """
    Load the player stats CSV for a given season, position, and situation.

    :param season: a str representing the season ('YYYY-YYYY')
    :param position: a str representing the player's position ('F', 'D', or 'G')
    :param situation: a str representing the game situation ('all', '5v5', '5v4', or '4v5')
    :return: DataFrame containing the player stats
    """
    stats_filename = f'{season}_{position}_{situation}_stats.csv'
    stats_file_path = os.path.join(DATA_DIR, 'data', 'stats', stats_filename)

    stats_df = pd.read_csv(stats_file_path)
    return stats_df


def load_rankings_csv(season: str, position: str, weighted: bool=True) -> pd.DataFrame:
    """
    Load the player rankings CSV for a given season and position.

    :param season: a str representing the season ('YYYY-YYYY')
    :param pos: a str representing the player's position ('F', 'D', or 'G')
    :param weighted: a bool to check if the weightings to load are yearly or weighted
    :return: DataFrame of the loaded rankings
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

    filename = f'{season}_{position}_{ranking_str}_rankings.csv'
    file_path = os.path.join(DATA_DIR, 'rankings', f'{ranking_str}_{pos_folder}', filename)
    
    ranking_df = pd.read_csv(file_path)
    return ranking_df


def save_csv(df: pd.DataFrame, main_folder: str, sub_folder: str, filename: str) -> None:
    """
    Save a DataFrame as a CSV file in a specified folder.

    :param df: DataFrame to save
    :param main_folder: Main folder name name inside DATA_DIR
    :param sub_folder: Subfolder name inside the main folder
    :param filename: Name of the CSV file to save
    :return: None
    """
    save_dir = os.path.join(DATA_DIR, main_folder, sub_folder)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, filename)

    df.to_csv(save_path, index=False)
    print(f"Saved {filename}")


def save_card(card: Image, season: str, team: str, position: str, filename: str) -> None:
    """
    Save a card PNG to a specified folder.

    :param card: The card image to save
    :param season: The season folder to save to
    :param team: The team folder inside the year folder to save to 
    :param position: The position folder inside the team folder to save to 
    :param filename: Name of the card to save
    :return: None
    """
    save_dir = os.path.join(DATA_DIR, 'cards', season, team, position)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, filename)

    card.save(save_path, 'PNG')
    print(f"Saved {filename}")