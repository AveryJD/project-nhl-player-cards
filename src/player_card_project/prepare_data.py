# ====================================================================================================
# SCRIPT TO GENERATE NHL PLAYER RANKINGS AND ASSEMBLE CARD DATA
# ====================================================================================================

# Imports
from player_card_project.utils import ranking
from player_card_project.utils import card_data
from player_card_project.utils import shift_data
from player_card_project.utils import player_stats
from player_card_project.utils import xgoals
from player_card_project.utils import rapm
from player_card_project.utils import war
from player_card_project.utils import constants


if __name__ == '__main__':

    # Train and save the xG model
    xgoals.make_and_save_xg_model()
    bundle = xgoals.load_xg_model()

    for season in constants.DATA_SEASONS:

        # Generate per-season teammate/competition TOI data
        shift_data.make_and_save_toi_matrices(season)

        # Assemble per-season player stats
        player_stats.make_and_save_all_stats(season, bundle=bundle)

        # Generate per-season RAPM scores
        rapm.make_and_save_rapm_scores_xg(season)

        # Generate per-season WAR scores
        war.make_and_save_war_scores(season, bundle=bundle)
        war.make_and_save_goalie_war_scores(season, bundle=bundle)

        # Generate per-season player rankings
        for pos in constants.POSITIONS:
            ranking.make_player_rankings(season, pos)

        # Generate weighted player rankings
        for pos in constants.POSITIONS:
            ranking.make_player_weighted_rankings(season, pos)

        # Assemble player card data
        for pos in constants.POSITIONS:
            card_data.make_card_data(season, pos)
