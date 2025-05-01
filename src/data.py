# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER PROFILES AND STATS DATA
# ====================================================================================================

# Imports
from utils import data_generation as data
from utils import constants


# Main loop to iterate through seasons and situations and get data
for season in constants.SEASONS:
    data.get_skater_profiles(season)
    data.get_goalie_profiles(season)
    for situation in constants.SITUATIONS:
        data.get_skater_stats(season, situation)
        data.get_goalie_stats(season, situation)

