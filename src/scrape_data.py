# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER BIOS AND STATS DATA
# ====================================================================================================

# Imports
from utils import collect_data as collect
from utils import clean_data as clean
from utils import constants
from utils import load_save


for season in constants.DATA_SEASONS:
    for position in constants.POSITIONS:
        collect.scrape_and_save_bios(season, position)
        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                collect.scrape_and_save_stats(season, position, situation)
        else:
            for situation in constants.GOALIE_SITUATIONS:
                collect.scrape_and_save_stats(season, position, situation)


"""
# For cleaning already scraped DataFrames
for season in constants.YEARLY_RANK_SEASONS:
    for position in constants.POSITIONS:

        bios_df = load_save.load_bios_csv(season, position)
        bios_df = clean.clean_dataframe(bios_df)
        bios_filename = f'{season}_{position}_bios.csv'
        load_save.save_csv(bios_df, 'data_scraped', 'bios', bios_filename)

        if position != 'G':
            for situation in constants.SKATER_SITUATIONS:
                stats_df = load_save.load_stats_csv(season, position, situation)
                stats_df = clean.clean_dataframe(stats_df)
                stats_filename = f'{season}_{position}_{situation}_stats.csv'
                load_save.save_csv(stats_df, 'data_scraped', 'stats', stats_filename)
        else:
            for situation in constants.GOALIE_SITUATIONS: 
                stats_df = load_save.load_stats_csv(season, position, situation)
                stats_df = clean.clean_dataframe(stats_df)
                stats_filename = f'{season}_{position}_{situation}_stats.csv'
                load_save.save_csv(stats_df, 'data_scraped', 'stats', stats_filename)
"""

