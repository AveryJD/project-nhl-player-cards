# ====================================================================================================
# CARD CREATION HELPER FUNCTIONS
# ====================================================================================================

# Imports
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR


def draw_centered_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        y_position: int,
        x_center: int = 1000,
        fill: tuple[int, int, int] = (0, 0, 0)
    ) -> None:    
    """
    Draws text that is centered on a PIL drawing.

    :param draw: a PIL drawing that will have the text centered on it
    :param text: a str of the text to be centered
    :param font: an ImageFont of the text's font
    :param y_position: an int of where the y position will be
    :param x_center: an int of where the center x position is (default is at 500)
    :param fill: a tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :return: None
    """

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = x_center - (text_width // 2)  
    draw.text((x_position, y_position), text, font=font, fill=fill)


def draw_righted_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    y_position: int,
    x_right: int,
    fill: tuple[int, int, int] = (0, 0, 0)
    ) -> None:
    """
    Draws text that right-aligned on a PIL drawing.

    :param draw: a PIL drawing that will have the text right-aligned on it
    :param text: a str of the text to be right-aligned
    :param font: an ImageFont of the text's font
    :param y_position: an int of where the y position will be
    :param x_center: an int of where the right most x position is
    :param fill: a tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :return: None
    """

    text_width = draw.textbbox((0, 0), str(text), font=font)[2] 
    x_position = x_right - text_width 
    draw.text((x_position, y_position), str(text), font=font, fill=fill)


def plot_to_image(fig: plt) -> Image:
    """
    Change a matplotlib plot into a PIL image.

    :param fig: a Matplotlib plot to be turned into an image
    :return: a PIL image of the plot
    """

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=500)
    buf.seek(0)
    img = Image.open(buf)

    return img


def get_word_date(number_date: str) -> str:
    """
    Converts a date from number format to word format (Ex: 2001-02-03 -> Feb 2, 2001).

    :param number_date: a str of date in number format (YYYY-MM-DD)
    :return: a str of the date in word format (Month Day, Year)
    """
    date_obj = datetime.strptime(number_date, '%Y-%m-%d')
    word_date = date_obj.strftime('%b %d, %Y')

    return word_date


def get_rank_and_percentile(player_row: pd.Series, attribute_rank_name: str, total_players: int) -> tuple[int, int]:
    """
    Return the player's rank and percentile of a given attribute.
    If a player does not qualify for an attribute ranking they will receive a rank of 'N/A'
    and their percentile will be 100 so that they receive a full percentile bar on their card.

    :param player_row: a series from a data frame containing player ranks
    :param attribute_rank_name: a str of the attribute name of the rank to return
    :param total_players: an int of the total players that qualify for the attribute
    :return: a tuple of the player's rank and percentile for the given attribute
    """
    # For player's that do not qualify for certain attributes (power play, penalty kill, and faceoffs)
    if attribute_rank_name in ["ppl_rank", "pkl_rank", "fof_rank"] and pd.isna(player_row[attribute_rank_name]):
        rank = 'N/A'
        percentile = 100
    # For attributes that all players qualify fore
    else:
        rank = int(player_row[attribute_rank_name])
        percentile = int(round((total_players - rank) / total_players, 2) * 100)

    return rank, percentile


def get_percentile_color(percentile: int) -> tuple[float, float, float]:
    """
    Return an RGB color based on the percentile rank.
    0%   -> Red (255, 0, 0)
    25%  -> Orange (255, 165, 0)
    50%  -> Yellow (255, 255, 0)
    75%  -> Light Green (144, 238, 144)
    100% -> Dark Green (0, 128, 0)

    :param percentile: an int of the percentile to return the color for
    :return: a tuple containing normalized RGB values that correspond to the given percentile
    """
    if percentile <= 25:
        # Get color between red (255,0,0) and orange (255,165,0)
        ratio = percentile / 25
        r = 255
        g = int(165 * ratio)
        b = 0
    elif percentile <= 50:
        # Get color between orange (255,165,0) and yellow (255,255,0)
        ratio = (percentile - 25) / 25
        r = 255
        g = 165 + int(90 * ratio)
        b = 0
    elif percentile <= 75:
        # Get color between yellow (255,255,0) and light green (144,238,144)
        ratio = (percentile - 50) / 25
        r = 255 - int((255 - 144) * ratio)
        g = 255 - int((255 - 238) * ratio)
        b = int(144 * ratio)
    else:
        # Get color between light green (144,238,144) and dark green (0,128,0)
        ratio = (percentile - 75) / 25
        r = 144 - int(144 * ratio)
        g = 238 - int((238 - 128) * ratio)
        b = 144 - int(144 * ratio)

    return (r, g, b)


def get_total_players(season_data: pd.DataFrame, pos: str, attribute: str,) -> int:
    """
    Return the total amount of players that qualify for the given attribute rank 
    (some players are not given a rank for certain attributes).

    :param season_data: a DataFrame of player stats
    :param pos: a str of the player's position's first letter ('F', 'D', or 'G')
    :param attribute: a str of the attribute to return the total players for
    :return: an int of the total players that are included in an attribute
    """
    # Total players for when attribute is not a special case or for any goalie attriibutes is all players
    if attribute not in ['ppl', 'pkl', 'fof'] or pos == 'G':
        total_players = len(season_data)

    # For attributes that not all players qualify for, ignore players whose attribute score is NAN
    else:
        score_column = f"{attribute}_rank"
        total_players = season_data[score_column].notna().sum()


    return total_players


def get_yearly_total_players(season: str, cur_season_data: pd.DataFrame, pos: str, seasons_num: int=5) -> dict[str, int]:
    """
    Return the total number of players for multiple past seasons based on different attributes.

    :param season: a str of the most recent season ('YYYY-YYYY')
    :param cur_season_data: a DataFrame containing player stats for the given season
    :param pos: a str of the first letter of the player's position ('F', 'D', or 'G')
    :param seasons_num: an int specifying the number of past seasons to retrieve player totals for (default is 5)
    :return: a dict mapping attribute-year keys to the corresponding total number of players
    """

    # Initialize dictionary, initial season, and initial data
    yearly_total_players = {}
    tot_players_season = season
    tot_players_season_data = cur_season_data

    # Set which attributes to count players by depending on position
    if pos != 'G':
        attribute_list = ['all', 'ppl', 'pkl', 'fof']
    else:
        attribute_list = ['all']

    # Iterate through the specified number of past seasons and get total players per attribute
    for _ in range(seasons_num):
        for attribute in attribute_list:
            value = get_total_players(tot_players_season_data, pos, attribute)
            yearly_total_players[f'{attribute}_{tot_players_season}'] = int(value)
        
        # Get previous season str
        tot_players_season = file.get_prev_season(tot_players_season)
        
        # Load data from previous season, but break if the file is not found
        try:
            tot_players_season_data = file.load_card_data_csv(tot_players_season, pos)
        except FileNotFoundError:
            print(f'Warning: Data for {tot_players_season} total players not found. Stopping iteration.')
            break

    return yearly_total_players


def get_player_multiple_seasons(player_name: str, cur_season: str, pos: str, seasons_num: int = 5) -> pd.DataFrame:
    """
    Return a DataFrame of a player's rankings for multiple consecutive seasons.

    :param player_name: a str of the full name of the player to return the multiple seasons for ('First Last')
    :param cur_season: a str of the most recent season ('YYYY-YYYY')
    :param pos: a str of the player's position's first letter ('F', 'D', or 'G')
    :param seasons_num: an int of the number of seasons to include (default is 5)
    :return: a DataFrame containing player stats and total player counts over the specified seasons
    """

    # Load the current season's data
    season_zero_data = file.load_card_data_csv(cur_season, pos)
    
    # Get player row
    player_seasons = season_zero_data[season_zero_data['Player'] == player_name].copy()

    # Initialize total players dictionary
    yearly_total_players = get_yearly_total_players(cur_season, season_zero_data, pos, seasons_num)

    # Add total players stats for the current season
    player_seasons['all_players'] = yearly_total_players.get(f'all_{cur_season}', 0)

    if pos == 'G':
        player_seasons['ppl_players'] = yearly_total_players.get(f'all_{cur_season}', 0)
        player_seasons['pkl_players'] = yearly_total_players.get(f'all_{cur_season}', 0)
        player_seasons['fof_players'] = yearly_total_players.get(f'all_{cur_season}', 0)
    else:
        player_seasons['ppl_players'] = yearly_total_players.get(f'ppl_{cur_season}', 0)
        player_seasons['pkl_players'] = yearly_total_players.get(f'pkl_{cur_season}', 0)
        player_seasons['fof_players'] = yearly_total_players.get(f'fof_{cur_season}', 0)
    

    # Loop to get previous seasons data
    season = file.get_prev_season(cur_season)
    for _ in range(seasons_num):
        try:
            season_data = file.load_card_data_csv(season, pos)
        except FileNotFoundError:
            print(f"Warning: Data for {season} season not found. Skipping this season.")
            break

        player_row = season_data[season_data['Player'] == player_name]
        if not player_row.empty:
            # Add player row to the DataFrame
            player_row = player_row.copy()
            player_row['all_players'] = yearly_total_players.get(f'all_{season}', 0)
            if pos != 'G':
                player_row['ppl_players'] = yearly_total_players.get(f'ppl_{season}', 0)
                player_row['pkl_players'] = yearly_total_players.get(f'pkl_{season}', 0)
                player_row['fof_players'] = yearly_total_players.get(f'fof_{season}', 0)
            player_seasons = pd.concat([player_seasons, player_row], ignore_index=True)

        # Move to the previous season
        season = file.get_prev_season(season)

    return player_seasons

