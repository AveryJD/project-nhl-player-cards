# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER CARDS
# ====================================================================================================

# Imports
from player_card_project.utils import card_generation

"""
Different functions for generating player cards:

card_generation.make_player_card('Sidney Crosby', '2025-2026', 'F', 'dark')
card_generation.make_team_player_cards('TOR', '2025-2026', 'light')
card_generation.make_all_player_cards('2025-2026', 'light')
"""


if __name__ == '__main__':

    card_generation.make_player_card('Sidney Crosby', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('Sidney Crosby', '2025-2026', 'F', 'light')

    card_generation.make_player_card('Macklin Celebrini', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('Macklin Celebrini', '2025-2026', 'F', 'light')

    card_generation.make_player_card('Miro Heiskanen', '2025-2026', 'D', 'dark')
    card_generation.make_player_card('Miro Heiskanen', '2025-2026', 'D', 'light')

    card_generation.make_player_card('David Pastrnak', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('David Pastrnak', '2025-2026', 'F', 'light')

    card_generation.make_player_card('Adam Fox', '2025-2026', 'D', 'dark')
    card_generation.make_player_card('Adam Fox', '2025-2026', 'D', 'light')
