# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD CREATION
# ====================================================================================================

# Imports
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import cairosvg
from PIL import Image, ImageDraw, ImageFont
from utils import card_helpers as ch
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR

# Load and cache fonts
BASIC_FONT_PATH = f'{DATA_DIR}/data_card/fonts/basic.ttf'
HEADING_FONT_PATH = f'{DATA_DIR}/data_card/fonts/header.ttf'

FONT_CACHE = {
    'basic_40': ImageFont.truetype(BASIC_FONT_PATH, 40),
    'basic_50': ImageFont.truetype(BASIC_FONT_PATH, 50),
    'basic_55': ImageFont.truetype(BASIC_FONT_PATH, 55),
    'basic_58': ImageFont.truetype(BASIC_FONT_PATH, 58),
    'basic_70': ImageFont.truetype(BASIC_FONT_PATH, 70),
    'basic_160': ImageFont.truetype(BASIC_FONT_PATH, 160),
    'heading_55': ImageFont.truetype(HEADING_FONT_PATH, 55),
    'heading_65': ImageFont.truetype(HEADING_FONT_PATH, 65),
    'heading_116': ImageFont.truetype(HEADING_FONT_PATH, 116),
}


def make_header_section(player_row: pd.Series) -> Image:
    """
    Creates the header section of a player card as a PIL Image. The header includes player profile information, team and season 
    banner, headshot, team logo, contract status (placeholder), and key stats.

    :param player_row: A Series containing player data
    :return: An Image of the header section
    """

    # Get banner variables
    name = player_row['Player']
    header_name = name
    for symbol, replacement in constants.SYMBOLS_TO_REPLACE.items():
        header_name = header_name.replace(symbol, replacement)
    season = player_row['Season']
    team = player_row['Team']
    team_full_name = constants.TEAM_NAMES.get(team)
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    secondary_team_color = constants.SECONDARY_COLORS.get(team)

    # Get profile variables
    player_id = player_row['Player ID']
    position = player_row['Position']
    position_name = constants.POSITION_NAMES.get(position)
    age = int(player_row['Age'])
    birth_date = ch.get_word_date(player_row['Date of Birth'])
    height = f"{int(player_row['Height (in)']) // 12}\'{int(player_row['Height (in)']) % 12}\""
    weight = f"{int(player_row['Weight (lbs)'])} lbs"
    draft_year = player_row['Draft Year']
    if draft_year == '-':
        draft_year = 'N/A'
        draft_position = 'Undrafted'
    else:
        draft_round = player_row['Draft Round']
        draft_pick = player_row['Round Pick']
        draft_overall = player_row['Overall Draft Position']
        draft_position = f'Round {draft_round}, Pick {draft_pick} ({draft_overall})'
    if pd.isna(player_row['Nationality']):
        nationality = constants.NATIONALITIES.get(player_row['Birth Country'])
    else:
        nationality = constants.NATIONALITIES.get(player_row['Nationality'])

    # Get stats variables
    role = player_row['Role']
    games_played = player_row['GP']
    if position != 'G':
        goals = player_row['Goals']
        primary_assists = player_row['First Assists']
        primary_points = goals + primary_assists
    else:
        save_percentage = format(float(player_row['SV%']), '.3f')
        goals_against_avg = format(player_row['GAA'], '.2f')
        xgoals_against = player_row['xG Against']
        goals_against = player_row['Goals Against']
        gsax = format(xgoals_against - goals_against, '.2f')

    # Create header section card
    header_section_width = 2000
    header_section_height = 700
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=(255, 255, 255))

    # Create draw object
    draw = ImageDraw.Draw(header_section)
    
    # Get team logo
    with open(f'data_card/team_logos/{team}.svg', 'rb') as f:
        svg_bytes = f.read()
    team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert("RGBA")

    # Calculate proportional height, resize and paste
    logo_width = 560
    w_percent = logo_width / team_logo.width
    logo_height = int(team_logo.height * w_percent)
    team_logo = team_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    header_section.paste(team_logo, (70, 200), team_logo)

    # Get player image and paste
    headshot_img = ch.get_player_headsot(season, team, player_id)
    headshot_img = headshot_img.resize((500, 500))
    header_section.paste(headshot_img, (100, 160), headshot_img)

    # Load fonts
    basic_font = FONT_CACHE['basic_40']
    banner_font = FONT_CACHE['heading_55']
    subheading_font = FONT_CACHE['heading_65']
    heading_font = FONT_CACHE['heading_116']
    
    # Draw subheaders text
    ch.draw_centered_text(draw, 'PROFILE', font=subheading_font, y_position=180, x_center=1000)
    ch.draw_centered_text(draw, 'STATS', font=subheading_font, y_position=180, x_center=1650)
    ch.draw_centered_text(draw, 'CONTRACT', font=subheading_font, y_position=420, x_center=1650)

    # Draw profile segment text
    draw.text(xy=(680, 270), text='POSITION:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 310), text='AGE:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 350), text='DATE OF BIRTH:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 390), text='HEIGHT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 430), text='WEIGHT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 470), text='DRAFT YEAR:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 510), text='DRAFT POSITION:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 550), text='NATIONALITY:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, text=position_name, font=basic_font, y_position=270, x_right=1320)
    ch.draw_righted_text(draw, text=age, font=basic_font, y_position=310, x_right=1320)
    ch.draw_righted_text(draw, text=birth_date, font=basic_font, y_position=350, x_right=1320)
    ch.draw_righted_text(draw, text=height, font=basic_font, y_position=390, x_right=1320)
    ch.draw_righted_text(draw, text=weight, font=basic_font, y_position=430, x_right=1320)
    ch.draw_righted_text(draw, text=draft_year, font=basic_font, y_position=470, x_right=1320)
    ch.draw_righted_text(draw, text=draft_position, font=basic_font, y_position=510, x_right=1320)
    ch.draw_righted_text(draw, text=nationality, font=basic_font, y_position=550, x_right=1320)

    # Draw banner
    draw.polygon([(20, 20), (1980, 20), (1940, 140), (60, 140)], fill=primary_team_color)
    # Draw name, team, and season drop shadow
    draw.text(xy=(76, 28), text=header_name, font=heading_font, fill=secondary_team_color)
    ch.draw_righted_text(draw, season, banner_font, 35, 1916, fill=secondary_team_color)
    ch.draw_righted_text(draw, team_full_name, banner_font, 80, 1916, fill=secondary_team_color)
    # Draw name and season text
    draw.text(xy=(80, 24), text=header_name, font=heading_font, fill=(255,255,255))
    ch.draw_righted_text(draw, season, banner_font, 33, 1918, fill=(255, 255, 255))
    ch.draw_righted_text(draw, team_full_name, banner_font, 78, 1918, fill=(255, 255, 255))

    # Draw stats segment text
    if position != 'G':
        draw.text(xy=(1400, 270), text='ROLE:', font=basic_font, fill=(0,0,0))
        draw.text(xy=(1400, 310), text='GP-G-A1-P1:', font=basic_font, fill=(0,0,0))

        ch.draw_righted_text(draw, text=role, font=basic_font, y_position=270, x_right=1900)
        ch.draw_righted_text(draw, text=f'{games_played}-{goals}-{primary_assists}-{primary_points}', font=basic_font, y_position=310, x_right=1900)

    else:
        draw.text(xy=(1400, 270), text='ROLE:', font=basic_font, fill=(0,0,0))
        draw.text(xy=(1400, 310), text='SV%-GAA-GSAx:', font=basic_font, fill=(0,0,0))

        ch.draw_righted_text(draw, text=f'{role} ({games_played} GP)', font=basic_font, y_position=270, x_right=1900)
        ch.draw_righted_text(draw, text=f'{save_percentage}-{goals_against_avg}-{gsax}', font=basic_font, y_position=310, x_right=1900)

    # Draw salary segment text
    draw.text(xy=(1400, 510), text='CAP HIT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(1400, 550), text='YEARS REMAINING:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, text='Coming Soon', font=basic_font, y_position=510, x_right=1900)   #f'${cap_hit:.3f} M'
    ch.draw_righted_text(draw, text='Coming Soon', font=basic_font, y_position=550, x_right=1900)   #contract_years_left

    # Draw divider rectangles
    draw.rectangle([(638, 200), (644, 600)], fill=secondary_team_color)
    draw.rectangle([(1356, 200), (1362, 600)], fill=secondary_team_color)
    draw.rectangle([(1400, 402), (1900, 408)], fill=secondary_team_color)

     # Draw bottom rectangle
    draw.rectangle([(60, 660), (1940, 700)], fill=primary_team_color)

    return header_section


def make_rank_component(player_row: pd.Series, attribute_rank_name: str) -> Image:
    """
    Creates a ranking component for a specific player attribute, displaying the player's rank, total players, 
    percentile, and a visual percentile bar.

    :param player_row: A Series containing player data
    :param attribute_rank_name: A str representing the name of the attribute that is being ranked (e.g. 'sht_rank')
    :return: An Image of the rank component
    """

    # Create ranking component card
    ranking_section_width = 300
    ranking_section_height = 240
    ranking_section = Image.new("RGB", (ranking_section_width, ranking_section_height), color=(255, 255, 255))

    # Create draw object 
    draw = ImageDraw.Draw(ranking_section)

    # Get attribute name text and color
    attribute_name = constants.ATTRIBUTE_NAMES.get(attribute_rank_name)
    if attribute_rank_name == 'pkl' and player_row['Position'] != 'G':
        attribute_color = (0,0,0)
    else:
        attribute_color = constants.ATTRIBUTE_COLORS.get(attribute_name)
    
    # Get rank and percentile
    if attribute_rank_name == 'ppl_rank':
        attribute_abrev = 'ppl'
    elif attribute_rank_name == 'pkl_rank':
        attribute_abrev = 'pkl'
    elif attribute_rank_name == 'fof_rank':
        attribute_abrev = 'fof'
    else:
        attribute_abrev = 'all'

    # Get total players
    total_players = int(player_row[f'{attribute_abrev}_players'])

    # Get rank and percentile
    rank, percentile = ch.get_rank_and_percentile(player_row, attribute_rank_name, total_players)
        
    # Get percentile color
    if rank == 'N/A':
        percentile_color = (100, 100, 100)
    else:
        percentile_color = ch.get_percentile_color(percentile)
    
    # Get percentile bar variables
    bar_x, bar_y = 210, 80
    bar_width, bar_height = 80, 160
    border = 5

    max_height = bar_height - 2 * border
    height = min(max(int(percentile * 1.5), 2), max_height)

    percent_left = bar_x + border
    percent_right = bar_x + bar_width - border
    percent_bottom = bar_y + bar_height - border
    percent_top = percent_bottom - height

    # Draw the percentile bar
    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
        fill=(230, 230, 230),
        outline=(200, 200, 200),
        width=border
    )

    draw.rectangle(
        [percent_left, percent_top, percent_right, percent_bottom],
        fill=percentile_color
    )

    # Load fonts
    attribute_name_font = FONT_CACHE['basic_55']
    rank_font = FONT_CACHE['basic_160']
    total_players_font = FONT_CACHE['basic_40']
    percentile_font = FONT_CACHE['basic_50']

    # Draw attribute name, rank, total players, and percentile texts
    ch.draw_centered_text(draw, attribute_name, attribute_name_font, fill=attribute_color, y_position=0, x_center=150)
    ch.draw_centered_text(draw, str(rank), rank_font, y_position=40, x_center=110)
    if rank != 'N/A':
        ch.draw_centered_text(draw, f'/ {total_players}', total_players_font, y_position=200, x_center=110)
        ch.draw_centered_text(draw, str(percentile), percentile_font, y_position=174, x_center=250)
    
    if attribute_name in ['5v4 Offense', '4v5 Defense', 'Even Strength', 'Penalty Kill']:
        # Draw dashed line
        draw.rectangle([(10, 64), (33, 70)], fill=attribute_color)
        draw.rectangle([(42, 64), (65, 70)], fill=attribute_color)
        draw.rectangle([(74, 64), (97, 70)], fill=attribute_color)
        draw.rectangle([(106, 64), (129, 70)], fill=attribute_color)
        draw.rectangle([(138, 64), (161, 70)], fill=attribute_color)
        draw.rectangle([(170, 64), (193, 70)], fill=attribute_color)
        draw.rectangle([(202, 64), (225, 70)], fill=attribute_color)
        draw.rectangle([(234, 64), (257, 70)], fill=attribute_color)
        draw.rectangle([(266, 64), (289, 70)], fill=attribute_color)

        # Draw circles at both ends
        r = 9
        draw.ellipse([(10 - r, 64 + 3 - r), (10 + r, 64 + 3 + r)], fill=attribute_color)
        draw.ellipse([(289 - r, 64 + 3 - r), (289 + r, 64 + 3 + r)], fill=attribute_color)

    elif attribute_name in ['5v5 Offense', '5v5 Defense', 'Overall', 'Even Strength']:
        # Draw rectangle
        draw.rectangle([(10, 64), (290, 70)], fill=attribute_color)

        # Draw circles at both ends
        r = 9
        draw.ellipse([(10 - r, 64 + 3 - r), (10 + r, 64 + 3 + r)], fill=attribute_color)
        draw.ellipse([(290 - r, 64 + 3 - r), (290 + r, 64 + 3 + r)], fill=attribute_color)

    else:
        # Draw rectangle
        draw.rectangle([(10, 64), (290, 70)], fill=attribute_color)

    plt.close()
    
    return ranking_section


def make_graph_section(player_multiple_seasons: pd.DataFrame, pos: str) -> Image:
    """
    Creates the graph section Image for the player card. The rank section contains a graph that displays the some of player's attribute rankings 
    over multiple seasons.

    :param player_multiple_seasons: A DataFrame containing player data over multiple seasons
    :param pos: A str of the first letter of the player's position ('F', 'D', or 'G')
    :return: An Image of the graph section
    """

    # Create graph component card
    graph_section_width = 1180
    graph_section_height = 650
    graph_section = Image.new("RGB", (graph_section_width, graph_section_height), color=(255, 255, 255))

    # Define attributes top plot depending on the position
    if pos != 'G':
        attributes_to_plot = ['evd', 'evo', 'pkl','ppl']
    else:
        attributes_to_plot = ['all', 'evs', 'gpk']

    # Make a list with the current season
    cur_season = max(player_multiple_seasons['Season'])
    
    # Add the previous four seasons to the list and put the oldest season first
    seasons = [cur_season]
    for _ in range(4):
        seasons.append(file.get_prev_season(seasons[-1]))
    seasons.reverse()

    # Store x-axis positions (fixed for 5 seasons)
    x_vals = list(range(1, 16, 3))

     # Create the figure with correct size
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(graph_section_width / 200, graph_section_height / 200), dpi=200)

    # Iterate over attributes
    for attribute_name in attributes_to_plot:
        percentiles = []
        for season in seasons:
            season_rows = player_multiple_seasons[player_multiple_seasons['Season'] == season]
            if not season_rows.empty:
                cur_player_row = season_rows.iloc[0]
                
                # Check if attribute data exists and keep track of percentiles to graph
                attr_rank_col = f"{attribute_name}_rank"
                if pd.notna(cur_player_row.get(attr_rank_col)) and cur_player_row.get(attr_rank_col) != 'N/A':
                    if attribute_name not in ['ppl', 'pkl', 'fof']:
                        total_players = cur_player_row.get('all_players')
                    else:
                        total_players = cur_player_row.get(f'{attribute_name}_players')
                    if pd.notna(total_players) and total_players > 0:
                        rank, percentile = ch.get_rank_and_percentile(cur_player_row, attr_rank_col, total_players)
                        if rank == 'N/A':
                            percentiles.append(None)
                        else:
                            percentiles.append(percentile)
                    else:
                        percentiles.append(None)
                else:
                    percentiles.append(None)
            else:
                percentiles.append(None)


        # Plot lines
        dashed_line_attributes = ['ppl', 'pkl', 'evs', 'gpk']

        valid_data = [(x, y) for x, y in zip(x_vals, percentiles) if y is not None]
        if valid_data:
            if attribute_name in dashed_line_attributes:
                x_plot, y_plot = zip(*valid_data)
                ax.plot(x_plot, y_plot, linewidth=2, linestyle='--', marker='o', markersize=6, color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_name}_plot'), alpha=1)
            else:
                x_plot, y_plot = zip(*valid_data)
                ax.plot(x_plot, y_plot, linewidth=4, linestyle='-', marker='o', markersize=9, color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_name}_plot'), alpha=1)
    

    # X-axis settings
    ax.set_xticks(x_vals)
    ax.set_xticklabels(seasons, fontsize=15, fontweight='bold')
    ax.tick_params(axis='x', labelsize=10, length=9, direction='inout')
    ax.set_xlim(min(x_vals) - 1, max(x_vals) + 1)

    # Y-axis settings
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylim(-2, 103)
    ax.tick_params(axis='y', labelsize=15, labelcolor='lightgrey', length=0, pad=-1)
    ax.set_yticklabels([0, 25, 50, 75, 100], fontsize=15, fontweight='bold', color='lightgrey')

    # Grid & Borders
    ax.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle="-", linewidth=2, color='lightgrey')
    ax.grid(axis='x', visible=False)

    plt.tight_layout()

    # Convert plot to image
    graph_img = ch.plot_to_image(fig)
    graph_img = graph_img.resize((graph_section_width, graph_section_height))
    graph_section.paste(graph_img, (0, 0))

    plt.close(fig)

    return graph_section


def make_branding_section(team: str) -> Image:
    """
    Creates the branding section Image for the player card. The branding section contains references to my website and socials, references to data sources,
    and and is stylized using the specified team's colors.

    :param team: A str representing the team abbreviation for the team to base the design color (e.g. 'TOR')
    :return: An Image of branding section
    """

    # Create branding section card
    branding_section_width = 2000
    branding_section_height = 400
    branding_section = Image.new("RGB", (branding_section_width, branding_section_height), color=(255, 255, 255))

    # Create draw image
    draw = ImageDraw.Draw(branding_section)

    # Get the font
    basic_font = FONT_CACHE['basic_55']
    
    # Branding text
    draw.text(xy=(100, 73), text='Website:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(100, 156), text='Socials:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, 'analyticswithavery.com', basic_font, 73, 940)
    ch.draw_righted_text(draw, 'analyticswavery', basic_font, 156, 940)

    # Resources text
    draw.text(xy=(1060, 73), text='Player Data From:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(1060, 156), text='Cap Data From:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, 'NaturalStatTrick.com', basic_font, 73, 1900)
    ch.draw_righted_text(draw, 'Coming Soon', basic_font, 156, 1900)  #'PuckPedia.com'
    
    # Get colors and fonts
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    secondary_team_color = constants.SECONDARY_COLORS.get(team)
    heading_font = basic_font = FONT_CACHE['heading_116']

    # Draw rectangles
    draw.rectangle([(60, 0), (1940, 40)], fill=primary_team_color)
    draw.rectangle([(998, 80), (1002, 220)], fill=secondary_team_color)

    # Draw branding shape
    draw.polygon([(60, 260), (1940, 260), (1980, 380), (20, 380)], fill=primary_team_color)
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=268, x_center=996, fill=secondary_team_color)
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=264, x_center=1000, fill=(255, 255, 255))

    return branding_section


def make_player_card(player_name: str, season: str, pos: str, save: bool=True) -> None:
    """
    Generate and save a full player card image for a given player and season.

    The player card includes a header section, ranking section, stat graph section,
    and a branding section. The card is saved as a PNG image in a directory
    specific to the season.

    :param player_name: A str of the full name of the player (e.g. 'Auston Matthews')
    :param season: A str of the season that the data for the card comes from('YYYY-YYYY')
    :param pos: A str of the first letter of the player's position ('F', 'D', or 'G')
    :return: None
    """

    # Get the data for a player's five seasons
    player_five_seasons = ch.get_player_multiple_seasons(player_name, season, pos)

    # Get the player's current season data
    player_cur_season = player_five_seasons.iloc[0]

    # Get the player's team
    team = player_cur_season['Team']

    # Get primary team color
    primary_team_color = constants.PRIMARY_COLORS.get(team)

    # Create player card
    card_width = 2000
    card_height = 2400
    player_card = Image.new('RGB', (card_width, card_height), color=(255, 255, 255))

    # Add header section
    header_section = make_header_section(player_cur_season)
    player_card.paste(header_section, (0, 0))

    # For skater cards
    if pos != 'G':
        # Add offense and defense rankings    
        evo_rank_section = make_rank_component(player_cur_season, 'evo_rank')
        player_card.paste(evo_rank_section, (50, 750))

        ppl_rank_section = make_rank_component(player_cur_season, 'ppl_rank')
        player_card.paste(ppl_rank_section, (455, 750))

        evd_rank_section = make_rank_component(player_cur_season, 'evd_rank')
        player_card.paste(evd_rank_section, (50, 1050))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl_rank')
        player_card.paste(pkl_rank_section, (455, 1050))

        # Add graph section
        graph_section = make_graph_section(player_five_seasons, pos)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add skill rankings
        oio_rank_section = make_rank_component(player_cur_season, 'oio_rank')
        player_card.paste(oio_rank_section, (50, 1425))

        sht_rank_section = make_rank_component(player_cur_season, 'sht_rank')
        player_card.paste(sht_rank_section, (455, 1425))

        scr_rank_section = make_rank_component(player_cur_season, 'scr_rank')
        player_card.paste(scr_rank_section, (850, 1425))

        plm_rank_section = make_rank_component(player_cur_season, 'plm_rank')
        player_card.paste(plm_rank_section, (1245, 1425))

        zon_rank_section = make_rank_component(player_cur_season, 'zon_rank')
        player_card.paste(zon_rank_section, (1640, 1425))

        oid_rank_section = make_rank_component(player_cur_season, 'oid_rank')
        player_card.paste(oid_rank_section, (50, 1715))

        pen_rank_section = make_rank_component(player_cur_season, 'pen_rank')
        player_card.paste(pen_rank_section, (455, 1715))

        phy_rank_section = make_rank_component(player_cur_season, 'phy_rank')
        player_card.paste(phy_rank_section, (850, 1715))

        fof_rank_section = make_rank_component(player_cur_season, 'fof_rank')
        player_card.paste(fof_rank_section, (1245, 1715))

        fan_rank_section = make_rank_component(player_cur_season, 'fan_rank')
        player_card.paste(fan_rank_section, (1640, 1715))

    # For goalie cards
    else:
        # Add overall rankings
        all_rank_section = make_rank_component(player_cur_season, 'all_rank')
        player_card.paste(all_rank_section, (253, 750))

        evs_rank_section = make_rank_component(player_cur_season, 'evs_rank')
        player_card.paste(evs_rank_section, (50, 1050))
    
        gpk_rank_section = make_rank_component(player_cur_season, 'gpk_rank')
        player_card.paste(gpk_rank_section, (455, 1050))

        # Add graph section
        graph_section = make_graph_section(player_five_seasons, pos)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add skill rankings
        ldg_rank_section = make_rank_component(player_cur_season, 'ldg_rank')
        player_card.paste(ldg_rank_section, (50, 1425))

        mdg_rank_section = make_rank_component(player_cur_season, 'mdg_rank')
        player_card.paste(mdg_rank_section, (455, 1425))

        hdg_rank_section = make_rank_component(player_cur_season, 'hdg_rank')
        player_card.paste(hdg_rank_section, (850, 1425))

        rbd_rank_section = make_rank_component(player_cur_season, 'rbd_rank')
        player_card.paste(rbd_rank_section, (1245, 1425))

        tmd_rank_section = make_rank_component(player_cur_season, 'tmd_rank')
        player_card.paste(tmd_rank_section, (1640, 1425))

        gre_rank_section = make_rank_component(player_cur_season, 'gre_rank')
        player_card.paste(gre_rank_section, (50, 1715))

        qal_rank_section = make_rank_component(player_cur_season, 'qal_rank')
        player_card.paste(qal_rank_section, (455, 1715))

        bad_rank_section = make_rank_component(player_cur_season, 'bad_rank')
        player_card.paste(bad_rank_section, (850, 1715))

        awf_rank_section = make_rank_component(player_cur_season, 'awf_rank')
        player_card.paste(awf_rank_section, (1245, 1715))

        fan_rank_section = make_rank_component(player_cur_season, 'fan_rank')
        player_card.paste(fan_rank_section, (1640, 1715))


    # Add branding section
    branding_section = make_branding_section(team)
    player_card.paste(branding_section, (0, 2000))

    if pos == 'F':
        pos_file = 'forwards' 
    elif pos == 'D':
        pos_file = 'defensemen'
    elif pos == 'G':
        pos_file = 'goalies'

    player_card = player_card.convert('RGB')

    file_name = f"{season}_{team}_{pos}_{player_name.replace(' ', '_')}.png"

    if save:
        file.save_card(player_card, season, team, pos_file, file_name)

    print(f'========== {player_name} ({team} {pos}) card created for the {season} season! ==========')

    return player_card

