# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER ATTRIBUTE RANKINGS
# ====================================================================================================

# Imports
from utils import rank_generation as rank
from utils import constants


for season in constants.SEASONS:
    for pos in constants.POSITIONS:
        rank.make_player_rankings(season, pos)

