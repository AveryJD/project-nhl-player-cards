# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER CARDS
# ====================================================================================================

# Imports
from utils import card_generation as card
from utils import constants

"""
Different functions for generating player cards:

card.make_player_card('Sidney Crosby', '2024-2025', 'F')
card.make_team_player_cards('TOR', '2024-2025')
card.make_position_player_cards('2024-2025', 'G')
card.make_rank_player_cards('evo', '2024-2025', 'D')
card.make_all_player_cards('2024-2025')
card.make_specific_player_cards(['Connor McDavid', 'Jack Hughes', 'Macklin Celebrini'], '2024-2025', 'F')
"""


# Generate Preview cards for the website
card.make_player_card('Sidney Crosby', '2024-2025', 'F')
card.make_player_card('Igor Shesterkin', '2024-2025', 'G')
card.make_player_card('Matthew Tkachuk', '2024-2025', 'F')
card.make_player_card('Miro Heiskanen', '2024-2025', 'D')
