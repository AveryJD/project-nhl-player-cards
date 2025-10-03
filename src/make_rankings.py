# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER ATTRIBUTE RANKINGS
# ====================================================================================================

# Imports
from utils import ranking
import utils.constants as constants


for season in constants.YEARLY_RANK_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_rankings(season, pos)

for season in constants.WEIGHTED_RANK_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_weighted_rankings(season, pos)
