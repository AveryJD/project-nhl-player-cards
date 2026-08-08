# ====================================================================================================
# SCRIPT TO SCRAPE ALL NHL PLAYER/GAME DATA
# ====================================================================================================

# Imports
from player_card_project.collect_data import collect_fonts
from player_card_project.collect_data import collect_logos
from player_card_project.collect_data import collect_players
from player_card_project.collect_data import collect_games
from player_card_project.collect_data import collect_stats
from player_card_project import constants



if __name__ == '__main__':

    # Scrape fonts from the web
    collect_fonts.scrape_fonts()

    # Scrape team logos from NHL.com
    collect_logos.scrape_logos()

    for season in constants.DATA_SEASONS:
            
        # Gather player IDs
        collect_players.scrape_player_ids(season)

        # Gather game schedule/results
        collect_games.scrape_schedule(season)

        # Gather regular-season team standings
        collect_games.scrape_team_standings(season)

        # Gather play-by-play data (goals, shot events, faceoffs, penalty events, and possession events)
        collect_stats.scrape_play_by_play(season)

        # Gather shift data
        collect_stats.scrape_shifts(season)

        # Gather GP/TOI and goalie situational stats
        collect_stats.scrape_boxscore(season)

        # Gather goalie game logs
        collect_stats.scrape_goalie_game_logs(season)

    # Gather general player bios from the NHL API
    collect_players.scrape_bios(constants.DATA_SEASONS)
