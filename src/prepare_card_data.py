# ====================================================================================================
# SCRIPT TO GENERATE THE INFORMATION USED FOR PLAYER CARDS
# ====================================================================================================

# Imports
from utils import card_data as info
from utils import constants


for season in constants.CARD_INFO_SEASONS:
    for pos in ['F', 'D']:
        info.make_card_data(season, pos)