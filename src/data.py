# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER BIOS AND STATS DATA
# ====================================================================================================

# Imports
from utils import data_generation as dg
from utils import constants


for season in constants.SEASONS:
    for position in constants.POSITIONS:
        dg.scrape_and_save_bios(season, position)
        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                dg.scrape_and_save_stats(season, position, situation)
        else:
            for situation in constants.GOALIE_SITUATIONS:
                dg.scrape_and_save_stats(season, position, situation)

