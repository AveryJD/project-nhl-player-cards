# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER BIOS AND STATS DATA
# ====================================================================================================

# Imports
from utils import collect_api_data as api
from utils import collect_nst_data as nst
from utils import clean_data as clean
from utils import constants
from utils import load_save as file


# Gather player IDs from the NHL API
for season in constants.DATA_SEASONS:
    api.get_player_ids(season)

# Gather goalie game logs from the NHL API
for season in constants.DATA_SEASONS:
    api.get_goalie_game_logs(season)

# Gather player bios and stats from NaturalStatTrick
for season in constants.DATA_SEASONS:
    for position in constants.POSITIONS:
        nst.scrape_and_save_bios(season, position)
        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                nst.scrape_and_save_stats(season, position, situation)
        else:
            for situation in constants.GOALIE_SITUATIONS:
                nst.scrape_and_save_stats(season, position, situation)

"""
# Clean CSV files that have already been gathered (if cleaning functionality has been updated and data does not need to be scraped again)
for season in constants.YEARLY_RANK_SEASONS:
    for position in constants.POSITIONS:

        bios_df = file.load_bios_csv(season, position)
        bios_df = clean.clean_dataframe(bios_df)
        bios_filename = f'{season}_{position}_bios.csv'
        file.save_csv(bios_df, 'data_scraped', 'bios', bios_filename)

        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                stats_df = file.load_stats_csv(season, position, situation)
                stats_df = clean.clean_dataframe(stats_df)
                stats_filename = f'{season}_{position}_{situation}_stats.csv'
                file.save_csv(stats_df, 'data_scraped', 'stats', stats_filename)
        else:
            for situation in constants.GOALIE_SITUATIONS: 
                stats_df = file.load_stats_csv(season, position, situation)
                stats_df = clean.clean_dataframe(stats_df)
                stats_filename = f'{season}_{position}_{situation}_stats.csv'
                file.save_csv(stats_df, 'data_scraped', 'stats', stats_filename)
"""

