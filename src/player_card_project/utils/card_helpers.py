# ====================================================================================================
# CARD CREATION HELPER FUNCTIONS
# ====================================================================================================

# Imports
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import numpy as np
from datetime import datetime
from player_card_project.utils import constants
from player_card_project.utils import load_save as file

DATA_DIR = constants.DATA_DIR


def draw_centered_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        y_position: int,
        x_center: int = 1000,
        fill: tuple[int, int, int] = (0, 0, 0),
        stroke_width: int = 0,
        stroke_fill: tuple[int, int, int] = None,
    ) -> None:
    """
    Draws text that is centered on a PIL drawing.

    :param draw: A PIL drawing that will have the text centered on it
    :param text: A str of the text to be centered
    :param font: An ImageFont of the text's font
    :param y_position: An int of where the y position will be
    :param x_center: An int of where the center x position is (default is at 1000)
    :param fill: A tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :param stroke_width: An int outline thickness in pixels around the text (default is 0/no outline)
    :param stroke_fill: A tuple of rgb values for the outline color (default is None)
    :return: None
    """

    text_bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = x_center - (text_width // 2)
    draw.text((x_position, y_position), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


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

    :param draw: A PIL drawing that will have the text right-aligned on it
    :param text: A str of the text to be right-aligned
    :param font: An ImageFont of the text's font
    :param y_position: An int of where the y position will be
    :param x_right: An int of where the right most x position is
    :param fill: A tuple of rgb values for the color of the text (default is (0,0,0)/black)
    :return: None
    """

    text_width = draw.textbbox((0, 0), str(text), font=font)[2] 
    x_position = x_right - text_width 
    draw.text((x_position, y_position), str(text), font=font, fill=fill)


def get_word_date(number_date: str) -> str:
    """
    Converts a date from number format to word format (Ex: 2001-02-03 -> Feb 2, 2001).

    :param number_date: A str of date in number format (YYYY-MM-DD)
    :return: A str of the date in word format (Month Day, Year)
    """
    date_obj = datetime.strptime(number_date, '%Y-%m-%d')
    word_date = date_obj.strftime('%b %d, %Y')

    return word_date


def plot_to_image(fig: plt.Figure) -> Image:
    """
    Change a matplotlib plot into a PIL image.

    :param fig: A Matplotlib plot to be turned into an image
    :return: A PIL image of the plot
    """

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=500)
    buf.seek(0)
    img = Image.open(buf)

    return img


def get_player_headshot(season: str, team: str, player_id: float) -> Image.Image:
    """
    Fetch a player's headshot image based on the season, team, and player ID.
    
    :param season: A str of the season to get the headshot for ('YYYY-YYYY')
    :param season: A str of the team abreviation to get the headshot for ('ABC')
    :param season: A float of the player ID to get the headshot for ('#######')
    :return: PIL Image object
    """

    season_clean = season.replace('-', '')
    if player_id is not None and not np.isnan(player_id):
        player_id_clean = str(int(player_id))
    else:
        player_id_clean = 000
    headshot_url = f"https://assets.nhle.com/mugs/nhl/{season_clean}/{team}/{player_id_clean}.png"

    try:
        response = requests.get(headshot_url, stream=True, timeout=5)
        response.raise_for_status()
        img_bytes = response.content
    except requests.RequestException:
        try:
            fallback_url = 'https://assets.nhle.com/mugs/nhl/default-skater.png'
            response = requests.get(fallback_url, stream=True, timeout=5)
            img_bytes = response.content
        except requests.RequestException:
            # Network unavailable — return a blank transparent image
            img = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
            return img

    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    img_data = img.getdata()
    img.putdata([
        (255, 255, 255, 0) if pixel[:2] == (255, 255, 255) else pixel
        for pixel in img_data
    ])

    return img


def get_rank_and_percentile(player_row: pd.Series, attribute_rank_name: str, total_players: int) -> tuple:
    """
    Return the player's rank and percentile of a given attribute.
    If a player does not qualify for an attribute ranking they will receive a rank of 'N/A'
    and their percentile will be 100 so that they receive a full percentile bar on their card.

    :param player_row: A series from a data frame containing player ranks
    :param attribute_rank_name: A str of the attribute name of the rank to return
    :param total_players: An int of the total players that qualify for the attribute
    :return: A tuple of the player's rank (int or 'N/A') and percentile (int) for the given attribute
    """
    # For player's that do not qualify for certain attributes (power play, penalty kill, or quality of competition/teammates)
    if attribute_rank_name in ["ppl_rank", "pkl_rank", "cmp_rank", "tmt_rank"] and pd.isna(player_row[attribute_rank_name]):
        rank = 'N/A'
        percentile = 100
    # For attributes that all players qualify for
    else:
        rank = int(player_row[attribute_rank_name])
        percentile = int(round((total_players - rank) / total_players, 2) * 100)

    return rank, percentile


def get_percentile_color(percentile: int) -> tuple[int, int, int]:
    """
    Return an RGB color based on the percentile rank.
    0%   -> Red (255, 0, 0)
    25%  -> Orange (255, 165, 0)
    50%  -> Yellow (255, 255, 0)
    75%  -> Light Green (144, 238, 144)
    100% -> Dark Green (0, 128, 0)

    :param percentile: An int of the percentile to return the color for
    :return: A tuple containing normalized RGB values that correspond to the given percentile
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


def get_player_single_season(player_name: str, cur_season: str, pos: str) -> pd.DataFrame:
    """
    Return a Series of a player's card data for a single season.

    :param player_name: A str of the full name of the player to return the multiple seasons for ('First Last')
    :param cur_season: A str of the most recent season ('YYYY-YYYY')
    :param pos: A str of the player's position's first letter ('F', 'D', or 'G')
    :return: A Series containing player stats for the given season
    """

    # Load the current season's card data
    season_data = file.load_card_data_csv(cur_season, pos)

    # Get player row
    player_season = season_data.loc[season_data['Player'] == player_name].copy()
    if player_season.empty:
        raise ValueError(f"{player_name} not found in {cur_season} {pos} card data.")
    player_season = player_season.iloc[0]

    return player_season
