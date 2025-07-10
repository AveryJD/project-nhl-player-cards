# ====================================================================================================
# FUNCTIONS FOR SCRAPING IMAGES
# ====================================================================================================

# Imports
import requests
from PIL import Image
from io import BytesIO


def get_team_image(team: str) -> Image:
    """
    Fetches and returns a team's logo image using the ESPN.com.

    :param team: str of the team abbreviation (ex., "TOR")
    :return: A PIL Image object of the team's logo
    """

    # Get URL for team logo
    # Special case where a player has played for multiple teams and their team str in the DataFrame has multiple teams (e.g. 'EDM,LAK')
    if ',' in team:
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/leagues/500/nhl.png&w=500&h=500&transparent=true'
    
    # Cases where team abreviations are different in the ESPN url
    elif team == 'LAK':
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/LA.png'
    elif team == "NJD":
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/NJ.png'
    elif team == "SJS":
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/SJ.png'
    elif team == "TBL":
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/TB.png'
    elif team == "UTA":
        team_url = 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/utah.png'
    
    else:
        team_url = f'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/{team}.png'
    
    # Get Image of the team logo
    response_team = requests.get(team_url, stream=True)
    if response_team.status_code == 200:
        team_img = Image.open(response_team.raw).convert("RGBA")
        team_img = Image.alpha_composite(
            Image.new("RGBA", team_img.size, (255, 255, 255, 255)), team_img
        )
    
    return team_img


def get_player_image(name: str, team: str, season: str, pos: str) -> Image:
    """
    Fetches and returns a player's headshot image using the NHL API.

    :param name: str of the player's full name (ex., "Matty Beniers")
    :param team: str of the team abbreviation (ex., "SEA")
    :param season: str of the season (ex., "2024-2025")
    :param pos: str of the first letter of the player's position (ex. 'F')
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
