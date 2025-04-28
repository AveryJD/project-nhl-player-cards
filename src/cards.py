# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER CARDS
# ====================================================================================================

import sys
DATA_DIR = '/Users/averyjdoiron/Documents/GitHub/NHL-Player-Stat-Cards'
sys.path.append(DATA_DIR)

# Imports
from src.utils import card_generation as card
from src.utils import constants



"""
Different functions for generating player cards:

card.make_player_card('Sidney Crosby', '2024-2025', 'f')
card.make_team_player_cards('TOR', '2024-2025')
card.make_position_player_cards('2024-2025', 'g')
card.make_rank_player_cards('off', '2024-2025', 'd')
card.make_all_player_cards('2024-2025')
card.make_specific_player_cards(constants.F_PLAYERS, '2024-2025', 'f')
"""
