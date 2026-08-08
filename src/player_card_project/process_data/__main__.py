# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER RANKINGS AND ASSEMBLE CARD DATA
# ====================================================================================================

# Imports
from player_card_project.process_data import shift_data
from player_card_project.process_data import xgoals
from player_card_project.process_data import rapm
from player_card_project.process_data import war
from player_card_project.process_data import player_stats
from player_card_project.process_data import player_ranking
from player_card_project.process_data import card_data
from player_card_project import constants



if __name__ == '__main__':

    # Train and save the xG model
    xgoals.make_and_save_xg_model()

    for season in constants.DATA_SEASONS:

        # Generate per-season teammate/competition TOI data
        shift_data.make_and_save_toi_matrices(season)

        # Assemble per-season player stats
        player_stats.make_and_save_all_stats(season)

        # Generate per-season RAPM scores
        rapm.make_and_save_rapm_scores_xg(season)

        # Generate per-season WAR scores
        war.make_war_scores(season)

        # Generate per-season player rankings
        for position in constants.POSITIONS:
            player_ranking.make_player_rankings(season, position)

        # Generate weighted player rankings
        for position in constants.POSITIONS:
            player_ranking.make_player_weighted_rankings(season, position)

        # Assemble player card data
        for position in constants.POSITIONS:
            card_data.make_card_data(season, position)
