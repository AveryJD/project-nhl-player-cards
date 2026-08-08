# ====================================================================================================
# FUNCTION FOR COLLECTING NHL TEAM LOGOS
# ====================================================================================================

# Imports
import requests
import os
import time
from player_card_project import constants



def scrape_logos() -> None:
    """
    Download every team's light/dark logo SVG from NHL.com into assets/team_logos. 
    'ATL' and 'PHX' aren't available this way and must be retrieved manually.
    
    :return: None
    """
    os.makedirs(f'{constants.DATA_DIR}/assets/team_logos', exist_ok=True)

    for team_code in constants.TEAM_NAMES:
        for variant in ['light', 'dark']:
            file_name = f"{team_code}_{variant}.svg"
            url = f'https://assets.nhle.com/logos/nhl/svg/{file_name}'
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                output_path = os.path.join(constants.DATA_DIR, 'assets', 'team_logos', file_name)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f'Saved {file_name}')

        # Brief delay to avoid hammering the NHL site
        time.sleep(0.10)
