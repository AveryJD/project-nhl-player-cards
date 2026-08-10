# ====================================================================================================
# FUNCTIONS FOR LOADING AND SAVING DIFFERENT FILES
# ====================================================================================================

# Imports
import pandas as pd
from PIL import Image
import os
from player_card_project import constants

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


def load_stats_csv(season: str, position: str, situation: str) -> pd.DataFrame:
    """
    Load the player stats CSV for a given season, position, and situation.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param situation: A str representing the game situation ('all', '5v5', '5v4', or '4v5')
    :return: The DataFrame containing the player stats
    """
    stats_file_name = f'{season}_{position}_{situation}_stats.csv'
    stats_file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'stats', stats_file_name)

    stats_df = pd.read_csv(stats_file_path)
    return stats_df


def load_rankings_csv(season: str, position: str, weighted: bool=True) -> pd.DataFrame:
    """
    Load the player rankings CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param weighted: A bool to check if the weightings to load are yearly or weighted
    :return: The DataFrame of the loaded rankings
    """
    if weighted:
        ranking_str = 'weighted'
    else:
        ranking_str = 'yearly'

    file_name = f'{season}_{position}_{ranking_str}_ranking.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', f'{ranking_str}_rankings', file_name)

    ranking_df = pd.read_csv(file_path)
    return ranking_df


def load_player_ids_csv(season: str) -> pd.DataFrame:
    """
    Load the player IDs CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the API information
    """
    player_ids_file_name = f'{season}_player_ids.csv'
    player_ids_file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'player_ids', player_ids_file_name)

    player_ids_df = pd.read_csv(player_ids_file_path)
    return player_ids_df


def load_player_bios_csv() -> pd.DataFrame:
    """
    Load the player bio CSV (one row per player, covers every season).

    :return: The DataFrame containing every scraped player's bio info
    """
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'player_bios', 'player_bios.csv')
    return pd.read_csv(file_path)


def load_shifts_csv(season: str) -> pd.DataFrame:
    """
    Load the raw shift chart CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's raw shift data
    """
    shifts_file_name = f'{season}_shifts.csv'
    shifts_file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'shifts', shifts_file_name)

    shifts_df = pd.read_csv(shifts_file_path)
    return shifts_df


def load_goals_csv(season: str) -> pd.DataFrame:
    """
    Load the raw goal-event CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's raw goal events
    """
    goals_file_name = f'{season}_goals.csv'
    goals_file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'goals', goals_file_name)

    goals_df = pd.read_csv(goals_file_path)
    return goals_df


def load_shot_events_csv(season: str) -> pd.DataFrame:
    """
    Load the raw shot-event CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's raw shot events
    """
    shot_events_file_name = f'{season}_shot_events.csv'
    shot_events_file_path = os.path.join(
        DATA_DIR, 'player_card_data', 'raw_data', 'shot_events', shot_events_file_name
    )

    shot_events_df = pd.read_csv(shot_events_file_path)
    return shot_events_df


def load_penalty_events_csv(season: str) -> pd.DataFrame:
    """
    Load the raw penalty-event CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's penalty events
    """
    file_name = f'{season}_penalty_events.csv'
    file_path = os.path.join(
        DATA_DIR, 'player_card_data', 'raw_data', 'penalty_events', file_name
    )
    return pd.read_csv(file_path)


def load_possession_events_csv(season: str) -> pd.DataFrame:
    """
    Load the raw hit/giveaway/takeaway event CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's raw possession events
    """
    file_name = f'{season}_possession_events.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'possession_events', file_name)
    return pd.read_csv(file_path)


def load_boxscore_skater_toi_csv(season: str) -> pd.DataFrame:
    """
    Load the per-game skater TOI/shift-count CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's per-game skater TOI
    """
    file_name = f'{season}_boxscore_skater_toi.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'boxscore', file_name)
    return pd.read_csv(file_path)


def load_boxscore_goalie_stats_csv(season: str) -> pd.DataFrame:
    """
    Load the per-game goalie strength-split shots/goals against CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's per-game goalie situational stats.
    """
    file_name = f'{season}_boxscore_goalie_stats.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'boxscore', file_name)
    return pd.read_csv(file_path)


def load_faceoffs_csv(season: str) -> pd.DataFrame:
    """
    Load the raw faceoff-event CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's raw faceoff events
    """
    file_name = f'{season}_faceoffs.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'faceoffs', file_name)

    faceoffs_df = pd.read_csv(file_path)
    return faceoffs_df


def load_schedule_csv(season: str) -> pd.DataFrame:
    """
    Load the season-level schedule CSV.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's schedule
    """
    file_name = f'{season}_schedule.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'schedule', file_name)

    schedule_df = pd.read_csv(file_path)
    return schedule_df


def load_rapm_scores_csv(season: str) -> pd.DataFrame:
    """
    Load a season's saved RAPM scores CSV.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's RAPM scores
    """
    file_name = f'{season}_rapm_scores.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'rapm_scores', file_name)

    rapm_scores_df = pd.read_csv(file_path)
    return rapm_scores_df


def load_skater_war_scores_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load a season's saved skater WAR scores CSV for one position -- forwards and defensemen are
    saved as separate files (see war.make_skater_war_scores), not a combined skaters file.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: 'F' or 'D'
    :return: The DataFrame containing the season's WAR scores for that position.
    """
    file_name = f'{season}_{position}_war_scores.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'war_scores', file_name)

    war_scores_df = pd.read_csv(file_path)
    return war_scores_df


def load_goalie_war_scores_csv(season: str) -> pd.DataFrame:
    """
    Load a season's saved goalie WAR scores CSV.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's goalie WAR scores
    """
    file_name = f'{season}_G_war_scores.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'war_scores', file_name)
    return pd.read_csv(file_path)


def load_teammate_toi_csv(season: str) -> pd.DataFrame:
    """
    Load the season-long teammate shared-TOI CSV.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing pairwise shared TOI between teammates
    """
    file_name = f'{season}_teammate_toi.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'shift_toi', file_name)

    teammate_toi_df = pd.read_csv(file_path)
    return teammate_toi_df


def load_competition_toi_csv(season: str) -> pd.DataFrame:
    """
    Load the season-long competition shared-TOI CSV.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing pairwise shared TOI between opponents
    """
    file_name = f'{season}_competition_toi.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'shift_toi', file_name)

    competition_toi_df = pd.read_csv(file_path)
    return competition_toi_df


def load_goalie_logs_csv(season: str) -> pd.DataFrame:
    """
    Load the goalie game logs CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the goalie game logs data
    """
    logs_file_name = f'{season}_goalie_logs.csv'
    logs_file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'goalie_logs', logs_file_name)

    logs_df = pd.read_csv(logs_file_path)
    return logs_df


def load_team_standings_csv(season: str) -> pd.DataFrame:
    """
    Load the team standings CSV for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame containing the season's team standings data
    """
    file_name = f'{season}_team_standings.csv'
    file_path = os.path.join(DATA_DIR, 'player_card_data', 'raw_data', 'team_standings', file_name)

    standings_df = pd.read_csv(file_path)
    return standings_df


def load_card_data_csv(season: str, position: str) -> pd.DataFrame:
    """
    Load the player card data CSV for a given season and position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :return: The DataFrame of the loaded card data
    """

    if position not in ('D', 'G'):
        position = 'F'
    pos_folder = constants.POSITION_FOLDERS[position]

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
    :param season: A str representing the season ('YYYY-YYYY')
    :param team: The team folder inside the year folder to save to
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param file_name: Name of the card to save
    :return: None
    """
    save_dir = os.path.join(PROJECT_DIR, 'player_cards', season, team, position)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file_name)

    card.save(save_path, 'PNG')
    print(f"Saved {file_name}")