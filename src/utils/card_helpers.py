# ====================================================================================================
# CARD CREATION HELPER FUNCTIONS
# ====================================================================================================

# Imports
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime


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