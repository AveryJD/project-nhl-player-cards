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



"""
# Clean data that has already been collected
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