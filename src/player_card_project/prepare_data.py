# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER RANKINGS AND ASSEMBLE CARD DATA
# ====================================================================================================

# Imports
from player_card_project.utils import ranking
from player_card_project.utils import card_data
from player_card_project.utils import constants


# Generate yearly rankings
for season in constants.CARD_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_rankings(season, pos)

# Generate weighted rankings
for season in constants.CARD_SEASONS:
    for pos in constants.POSITIONS:
        ranking.make_player_weighted_rankings(season, pos)

# Assemble card data
for season in constants.CARD_SEASONS:
    for pos in constants.POSITIONS:
        card_data.make_card_data(season, pos)
