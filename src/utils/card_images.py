# ====================================================================================================
# FUNCTIONS FOR SCRAPING IMAGES
# ====================================================================================================

# Imports
import requests
from PIL import Image
import cairosvg
from io import BytesIO
import os
from utils import constants

DATA_DIR = constants.DATA_DIR

def get_team_image(team: str) -> Image.Image:
    """
    Fetches and returns a team's logo image as a PNG (converted from SVG).

    :param team: A str of the team abbreviation (ex., "TOR")
    :return: A PIL Image object of the team's logo
    """

    if team != 'ATL':

        if team == 'PHX':
            team = 'ARI'

        # Get team logo url
        team_url = f'https://assets.nhle.com/logos/nhl/svg/{team}_light.svg'
        response_team = requests.get(team_url)

        # Convert SVG to PNG
        if response_team.status_code == 200:
            png_bytes = cairosvg.svg2png(bytestring=response_team.content)
            team_logo = Image.open(BytesIO(png_bytes)).convert("RGBA")

    else:
        team_logo_path = os.path.join(DATA_DIR, f"data_card/assets/{team}.svg")
        with open(team_logo_path, "rb") as svg_file:
            svg_data = svg_file.read()
            png_bytes = cairosvg.svg2png(bytestring=svg_data)
            team_logo = Image.open(BytesIO(png_bytes)).convert("RGBA")
    
    return team_logo



def get_player_image(name: str, team: str, season: str, pos: str) -> Image:
    """
    Fetches and returns a player's headshot image using the NHL API.

    :param name: A str of the player's full name (ex., "Matty Beniers")
    :param team: A str of the team abbreviation (ex., "SEA")
    :param season: A str of the season (ex., "2024-2025")
    :param pos:  A str of the first letter of the player's position (ex. 'F')
    :return: A PIL Image object of the player's headshot
    """

    # Format season correctly (removes hyphen)
    years = season.replace('-', '')

    # Get NHL API URL to fetch the team's roster
    api_team_page = f'https://api-web.nhle.com/v1/roster/{team}/{years}'

    # Fetch the team's roster data
    response = requests.get(api_team_page)
    
    if response.status_code != 200:
        print("Failed to fetch team roster.")
        return None

    roster_data = response.json()

    if pos == 'F':
        position = 'forwards'
    if pos == 'D':
        position = 'defensemen'
    if pos == 'G':
        position = 'goalies'
        
    # Search for the player by name
    for player in roster_data.get(position, []):  # Adjust for other positions if needed
        first_name = player["firstName"]["default"]
        last_name = player["lastName"]["default"]
        full_name = f"{first_name} {last_name}"

        if full_name.lower() == name.lower():
            headshot_url = player["headshot"]
            break
    # If player headshot is not found use a template image
    else:
        headshot_url = 'https://a.espncdn.com/combiner/i?img=/i/headshots/nophoto.png&w=110&h=80&scale=crop'


    # Fetch and process the player's headshot
    response = requests.get(headshot_url, stream=True)
    
    if response.status_code == 200:
        face_img = Image.open(BytesIO(response.content)).convert("RGBA")

        # Make image background transparent
        face_img_data = face_img.getdata()
        transparent_face = [
            (255, 255, 255, 0) if pixel[:3] == (255, 255, 255) else pixel
            for pixel in face_img_data
        ]
        face_img.putdata(transparent_face)
      
    return face_img
