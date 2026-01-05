# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER BIOS AND STATS DATA
# ====================================================================================================

# Imports
from utils import collect_api_data
from utils import collect_nst_data
from utils import collect_logos
from utils import constants


# Scrape logos from NHL.com
collect_logos.scrape_logos()


# Gather player IDs from the NHL API
for season in constants.DATA_SEASONS:
    collect_api_data.get_player_ids(season)


# Gather player bios and stats from NaturalStatTrick
for season in constants.DATA_SEASONS:
    for position in constants.POSITIONS:
        collect_nst_data.scrape_and_save_bios(season, position)
        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                collect_nst_data.scrape_and_save_stats(season, position, situation)
        else:
            for situation in constants.GOALIE_SITUATIONS:
                collect_nst_data.scrape_and_save_stats(season, position, situation)


# Gather goalie game logs from the NHL API
for season in constants.DATA_SEASONS:
    collect_api_data.get_goalie_game_logs(season)
