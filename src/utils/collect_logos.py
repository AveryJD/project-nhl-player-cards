# ====================================================================================================
# FUNCTION FOR COLLECTING NHL TEAM LOGOS
# ====================================================================================================

# Imports
import requests
import os
from utils import constants


def scrape_logos() -> None:
    """
    Iterates through team codes and logo variants to download SVG files.
    Currently 'ATL' and 'PHX' must be retreived

    :return: None
    """
    os.makedirs(f'{constants.DATA_DIR}/data_card/team_logos', exist_ok=True)
    
    for team_code in constants.TEAM_NAMES:
        for variant in ['light', 'dark']:
            # Make the full URL for the SVG file
            file_name = f"{team_code}_{variant}.svg"
            url = f'https://assets.nhle.com/logos/nhl/svg/{file_name}'
            
            # Make a GET request to the URL
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                # Write the SVG content to a file
                output_path = os.path.join(constants.DATA_DIR, 'data_card', 'team_logos', file_name)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f'Saved {file_name}')
