# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER ATTRIBUTE RANKINGS
# ====================================================================================================

# Imports
from utils import rank_generation as rank
from utils import constants


# Main loop to iterate through seasons and make player rankings
for season in constants.SEASONS:
    rank.make_skater_rankings(season)
    rank.make_goalie_rankings(season)

