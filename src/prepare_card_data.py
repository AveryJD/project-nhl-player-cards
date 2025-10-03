# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER ATTRIBUTE RANKINGS AND ASSEMBLE CARD DATA
# ====================================================================================================

# Imports
from utils import ranking
from utils import card_data as card
import utils.constants as constants


# Generate yearly rankings
for season in constants.YEARLY_RANK_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_rankings(season, pos)

# Generate weighted rankings
for season in constants.WEIGHTED_RANK_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_weighted_rankings(season, pos)

# Assemble card data
for season in constants.CARD_INFO_SEASONS:
    for pos in constants.POSITIONS:
        card.make_card_data(season, pos)
