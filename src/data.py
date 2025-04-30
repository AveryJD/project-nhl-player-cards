# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER PROFILES AND STATS DATA
# ====================================================================================================

import sys
DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'
sys.path.append(DATA_DIR)

# Imports
from src.utils import data_generation as data
from src.utils import constants


# Main loop to iterate through seasons and situations and get data
for season in constants.SEASONS:
    data.get_skater_profiles(season)
    data.get_goalie_profiles(season)
    for situation in constants.SITUATIONS:
        data.get_skater_stats(season, situation)
        data.get_goalie_stats(season, situation)

