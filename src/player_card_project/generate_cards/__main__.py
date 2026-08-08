# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER CARDS
# ====================================================================================================

# Imports
from player_card_project.generate_cards import card_generation



if __name__ == '__main__':

    card_generation.make_player_card('Sidney Crosby', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('Sidney Crosby', '2025-2026', 'F', 'light')

    card_generation.make_player_card('Moritz Seider', '2025-2026', 'D', 'dark')
    card_generation.make_player_card('Moritz Seider', '2025-2026', 'D', 'light')

    card_generation.make_player_card('David Pastrnak', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('David Pastrnak', '2025-2026', 'F', 'light')

    card_generation.make_player_card('Miro Heiskanen', '2025-2026', 'D', 'dark')
    card_generation.make_player_card('Miro Heiskanen', '2025-2026', 'D', 'light')

    card_generation.make_player_card('Nikita Kucherov', '2025-2026', 'F', 'dark')
    card_generation.make_player_card('Nikita Kucherov', '2025-2026', 'F', 'light')
