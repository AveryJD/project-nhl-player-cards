# ====================================================================================================
# SCRIPT TO SCRAPE ALL NHL PLAYER/GAME DATA
# ====================================================================================================

# Imports
from player_card_project.utils import collect_api_data
from player_card_project.utils import collect_logos
from player_card_project.utils import constants


if __name__ == '__main__':

    # Scrape team logos from NHL.com
    collect_logos.scrape_logos()

    for season in constants.DATA_SEASONS:

        # Gather player IDs
        collect_api_data.get_player_ids(season)

        # Gather goalie game logs
        collect_api_data.get_goalie_game_logs(season)

        # Gather play-by-play data (goals, shot events, faceoffs, penalty events, and possession events)
        collect_api_data.scrape_and_save_play_by_play(season)

        # Gather shift data
        collect_api_data.scrape_and_save_shifts(season, force_recheck=True)

        # Gather GP/TOI and goalie situational stats
        collect_api_data.scrape_and_save_boxscore(season)

        # Gather regular-season team standings
        collect_api_data.get_team_standings(season)

        # Gather game schedule/results
        collect_api_data.scrape_and_save_schedule(season)


    # Gather general player bios from the NHL API
    collect_api_data.scrape_bios()
