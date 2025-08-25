# ====================================================================================================
# SCRIPT TO GENERATE THE INFORMATION USED FOR PLAYER CARDS
# ====================================================================================================

# Imports
from utils import card_data as cd
from utils import constants


for season in constants.CARD_INFO_SEASONS:
    for pos in constants.POSITIONS:
        cd.make_card_data(season, pos)
