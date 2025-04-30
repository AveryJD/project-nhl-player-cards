# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER ATTRIBUTE RANKINGS
# ====================================================================================================

import sys
DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'
sys.path.append(DATA_DIR)

# Imports
from src.utils import rank_generation as rank
from src.utils import constants


# Main loop to iterate through seasons and make player rankings
for season in constants.SEASONS:
    rank.make_skater_rankings(season)
    rank.make_goalie_rankings(season)

