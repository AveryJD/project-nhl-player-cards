# ====================================================================================================
# FUNCTION FOR COLLECTING FONTS USED IN CARD GENERATION
# ====================================================================================================

# Imports
import requests
import os
import io
import zipfile
from player_card_project import constants


def scrape_fonts() -> None:
    """
    Download basic.ttf (League Gothic, from Google Fonts) and header.ttf (Basketball by Akhmad Afandhi, from dafont.com) into assets/fonts.

    :return: None
    """
    fonts_dir = os.path.join(constants.DATA_DIR, 'assets', 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)

    # League Gothic (basic.ttf)
    league_gothic_url = 'https://fonts.gstatic.com/s/leaguegothic/v13/qFdR35CBi4tvBz81xy7WG7ep-BQAY7Krj7feObpH_9ahg9A.ttf'
    response = requests.get(league_gothic_url, stream=True)
    response.raise_for_status()
    with open(os.path.join(fonts_dir, 'basic.ttf'), 'wb') as f:
        f.write(response.content)
    print('Saved basic.ttf')

    # Basketball (header.ttf)
    basketball_url = 'https://dl.dafont.com/dl/?f=basketball'
    response = requests.get(basketball_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        otf_name = next(name for name in archive.namelist() if name.lower().endswith('.otf'))
        with archive.open(otf_name) as src, open(os.path.join(fonts_dir, 'header.ttf'), 'wb') as f:
            f.write(src.read())
    print('Saved header.ttf')
