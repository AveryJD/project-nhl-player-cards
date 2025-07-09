# ====================================================================================================
# SCRIPT TO SCRAPE NHL PLAYER BIOS AND STATS DATA
# ====================================================================================================

# Imports
from utils import data_generation as dg
from utils import data_cleaning as dc
from utils import constants


for season in constants.SEASONS:

    for pos in constants.POSITIONS:
        
        # Scrape & save bios
        s_bio_url = dg.make_nst_url(season, situation='all', stdoi='bio', position=pos)
        s_bio_df = dg.scrape_data(s_bio_url)
        cleaned_s_bio_df = dc.clean_dataframe(s_bio_df)
        dg.save_data_csv(cleaned_s_bio_df, folder='bios', filename=f'{season}_{pos}_bios.csv')

        if pos != 'G':
            # Scrape & save skater stats
            for sit in constants.SKATER_SITUATIONS:
                std_url = dg.make_nst_url(season, situation=sit, stdoi='std', position=pos)
                std_df = dg.scrape_data(std_url)

                oi_url = dg.make_nst_url(season, situation=sit, stdoi='oi', position=pos)
                oi_df = dg.scrape_data(oi_url)

                merge_keys = ['Player', 'Team', 'Position', 'GP', 'TOI']
                stats_df = dg.merge_data(std_df, oi_df, merge_keys)
                cleaned_stats_df = dc.clean_dataframe(stats_df)

                dg.save_data_csv(cleaned_stats_df, folder='stats', filename=f'{season}_{pos}_{sit}_stats.csv')

        else:
            # Scrape & save goalie stats
            for sit in constants.GOALIE_SITUATIONS:
                g_stats_url = dg.make_nst_url(season, situation=sit, stdoi='g', position='G')
                g_stats_df = dg.scrape_data(g_stats_url)

                cleaned_g_stats_df = dc.clean_dataframe(g_stats_df)
                dg.save_data_csv(cleaned_g_stats_df, folder='stats', filename=f'{season}_G_{sit}_stats.csv')

