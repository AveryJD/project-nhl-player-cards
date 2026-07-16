# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD CREATION
# ====================================================================================================

# Imports
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import ast
import cairosvg
from PIL import Image, ImageDraw, ImageFont
from player_card_project.utils import card_helpers as ch
from player_card_project.utils import constants
from player_card_project.utils import load_save as file

DATA_DIR = constants.DATA_DIR

# Load and cache fonts
BASIC_FONT_PATH = f'{DATA_DIR}/assets/fonts/basic.ttf'
HEADING_FONT_PATH = f'{DATA_DIR}/assets/fonts/header.ttf'

FONT_CACHE = {
    'basic_40': ImageFont.truetype(BASIC_FONT_PATH, 40),
    'basic_50': ImageFont.truetype(BASIC_FONT_PATH, 50),
    'basic_73': ImageFont.truetype(BASIC_FONT_PATH, 73),
    'basic_150': ImageFont.truetype(BASIC_FONT_PATH, 150),
    'heading_50': ImageFont.truetype(HEADING_FONT_PATH, 50),
    'heading_70': ImageFont.truetype(HEADING_FONT_PATH, 70),
    'heading_116': ImageFont.truetype(HEADING_FONT_PATH, 116),
}


def make_header_section(player_row: pd.Series, mode: str = 'light') -> Image:
    """
    Creates the header section of a player card as a PIL Image. The header includes player profile information, team and season 
    banner, headshot, team logo, and key stats.

    :param player_row: A Series containing player data
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the header section
    """

    # Get the player's team    
    team = player_row['Team']

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        text_color = constants.DARK
    else:
        background_color = constants.DARK
        text_color = constants.WHITE
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    header_text_color = constants.WHITE
    header_shadow_color = constants.SECONDARY_COLORS.get(team)
    
    # Get banner variables
    name = player_row['Player']
    header_name = name
    for symbol, replacement in constants.SYMBOLS_TO_REPLACE.items():
        header_name = header_name.replace(symbol, replacement)
    season = player_row['Season']

    # Get profile variables
    player_id = player_row['Player ID']
    position = player_row['Position']
    specific_position = player_row.get('Specific Position')
    position_name = constants.SPECIFIC_POSITION_NAMES.get(specific_position, constants.POSITION_NAMES.get(position))
    role = player_row['Role']
    age = int(player_row['Age'])
    birth_date = ch.get_word_date(player_row['Date of Birth'])
    age_birthday = f'{age} ({birth_date})'
    size_str = f"{int(player_row['Height (in)']) // 12}\'{int(player_row['Height (in)']) % 12}\", {int(player_row['Weight (lbs)'])} lbs"

    # Compute stats for profile display
    games_played = int(player_row['GP'])
    games_played_str = str(games_played)
    if position != 'G':
        toi = float(player_row['TOI'])
        toi_per_gp = toi / games_played
        toi_minutes = int(toi_per_gp)
        toi_seconds = int((toi_per_gp - toi_minutes) * 60)
        toi_formatted = f"{toi_minutes}:{toi_seconds:02d}"
        stat_line = f"{int(player_row['Goals'])}-{int(player_row['Total Assists'])}-{int(player_row['Goals'] + player_row['Total Assists'])}"
        xgoals = format(player_row['ixG'], '.2f')
        xgoals_for_percent = format((player_row['xGF%'] / 100), '.3f')
    else:
        record = f"{player_row['W']}-{player_row['L']}-{player_row['OT/SO']}"
        save_percentage = format(float(player_row['SV%']), '.3f')
        gsax = format(player_row['xG Against'] - player_row['Goals Against'], '.2f')

    # Create header section card
    header_section_width = 2000
    header_section_height = 700
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=background_color)

    # Create draw object
    draw = ImageDraw.Draw(header_section)
    
    # Load fonts
    basic_font = FONT_CACHE['basic_50']
    heading_font = FONT_CACHE['heading_116']

    # x center for team logo and player headshot
    left_center_x = 362

    with open(f'data/assets/team_logos/{team}_{mode}.svg', 'rb') as f:
        svg_bytes = f.read()
    team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert("RGBA")
    logo_width = 808
    w_percent = logo_width / team_logo.width
    logo_height = int(team_logo.height * w_percent)
    team_logo = team_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    header_section.paste(team_logo, (left_center_x - logo_width // 2, 140), team_logo)

    headshot_size = 520
    headshot_img = ch.get_player_headsot(season, team, player_id)
    headshot_img = headshot_img.resize((headshot_size, headshot_size))
    # Crop transparent bottom padding then paste bottom-aligned so jerseys line up with header bottom bar
    bbox = headshot_img.getbbox()
    if bbox:
        headshot_img = headshot_img.crop((0, 0, headshot_img.width, bbox[3]))
    paste_y = 660 - headshot_img.height
    header_section.paste(headshot_img, (left_center_x - headshot_size // 2, paste_y), headshot_img)

    # Row y positions
    row_ys = [195, 248, 301, 354, 407, 460, 513, 566]
    x_right = 1562
    x_val   = 1612

    ch.draw_righted_text(draw, text='Position:', font=basic_font, y_position=row_ys[0], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Role:',     font=basic_font, y_position=row_ys[1], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Age:',      font=basic_font, y_position=row_ys[2], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Size:',   font=basic_font, y_position=row_ys[3], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Games:',   font=basic_font, y_position=row_ys[4], x_right=x_right, fill=text_color)

    draw.text(xy=(x_val, row_ys[0]), text=position_name,  font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[2]), text=age_birthday,   font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[3]), text=size_str,         font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[4]), text=games_played_str, font=basic_font, fill=text_color)

    if position != 'G':
        ch.draw_righted_text(draw, text='G-A-P:',  font=basic_font, y_position=row_ys[5], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='xG:',     font=basic_font, y_position=row_ys[6], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='xGF %:',  font=basic_font, y_position=row_ys[7], x_right=x_right, fill=text_color)
        draw.text(xy=(x_val, row_ys[1]), text=f'{role} ({toi_formatted})', font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[5]), text=stat_line,          font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[6]), text=xgoals,             font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[7]), text=xgoals_for_percent, font=basic_font, fill=text_color)
    else:
        ch.draw_righted_text(draw, text='W-L-OTL:', font=basic_font, y_position=row_ys[5], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='Save %:',  font=basic_font, y_position=row_ys[6], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='GSAx:',    font=basic_font, y_position=row_ys[7], x_right=x_right, fill=text_color)
        draw.text(xy=(x_val, row_ys[1]), text=role,            font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[5]), text=record,          font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[6]), text=save_percentage, font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[7]), text=gsax,            font=basic_font, fill=text_color)

    # Draw banner
    draw.polygon([(20, 20), (1980, 20), (1940, 140), (60, 140)], fill=primary_team_color)
    # Draw name and season drop shadow
    draw.text(xy=(76, 28), text=header_name, font=heading_font, fill=header_shadow_color)
    ch.draw_righted_text(draw, season, heading_font, 28, 1920, fill=header_shadow_color)
    # Draw name and season text
    draw.text(xy=(80, 24), text=header_name, font=heading_font, fill=header_text_color)
    ch.draw_righted_text(draw, season, heading_font, 24, 1924, fill=header_text_color)

    # Draw bottom rectangle
    draw.rectangle([(60, 660), (1940, 700)], fill=primary_team_color)

    return header_section


def make_rank_component(player_row: pd.Series, attribute_rank_name: str, mode: str = 'light') -> Image:
    """
    Creates a ranking component for a specific player attribute, displaying the player's rank, total players, 
    percentile, and a visual percentile bar.

    :param player_row: A Series containing player data
    :param attribute_rank_name: A str representing the name of the attribute that is being ranked (e.g. 'sht_rank')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the rank component
    """

    # Get attribute name
    attribute_name = constants.ATTRIBUTE_NAMES.get(attribute_rank_name)

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        text_color = constants.DARK
        if attribute_rank_name in ['tot_rank', 'evo_rank', 'evd_rank', 'evs_rank'] or (player_row['Position'] == 'G' and attribute_rank_name == 'pkl_rank'):
            attribute_color = constants.ATTRIBUTE_COLORS[attribute_name]
        else:
            attribute_color = constants.DARK
    else:
        background_color = constants.DARK
        text_color = constants.WHITE
        if attribute_rank_name in ['tot_rank', 'evo_rank', 'evd_rank', 'evs_rank'] or (player_row['Position'] == 'G' and attribute_rank_name == 'pkl_rank'):
            attribute_color = constants.ATTRIBUTE_COLORS[attribute_name]
        else:
            attribute_color = constants.WHITE

    # Create ranking component card
    ranking_section_width = 300
    ranking_section_height = 240
    ranking_section = Image.new("RGB", (ranking_section_width, ranking_section_height), color=background_color)

    # Create draw object 
    draw = ImageDraw.Draw(ranking_section)
    
    # Get attribute abbreviation
    if attribute_rank_name == 'ppl_rank':
        attribute_abbrev = 'ppl'
    elif attribute_rank_name == 'pkl_rank' and player_row.get('Position') != 'G':
        attribute_abbrev = 'pkl'
    else:
        attribute_abbrev = 'all'

    # Get total players
    total_players = int(player_row[f'{attribute_abbrev}_players'])

    # Get rank and percentile
    rank, percentile = ch.get_rank_and_percentile(player_row, attribute_rank_name, total_players)
        
    # Get percentile color
    if rank == 'N/A':
        percentile_color = (100, 100, 100)
    else:
        percentile_color = ch.get_percentile_color(percentile)
    
    # Get percentile bar variables
    bar_x, bar_y = 210, 82
    bar_width, bar_height = 78, 150
    border = 2

    height = percentile * 1.5

    percent_left = bar_x
    percent_right = bar_x + bar_width
    percent_bottom = bar_y + bar_height
    percent_top = percent_bottom - height

    # Draw the percentile bar
    draw.rectangle([bar_x - border, bar_y - border, bar_x + bar_width + border, bar_y + bar_height + border], 
                   fill=constants.GRAY, outline=text_color, width=border)
    draw.rectangle([percent_left, percent_top, percent_right, percent_bottom], fill=percentile_color)

    # Load fonts
    attribute_name_font = FONT_CACHE['basic_73']
    rank_font = FONT_CACHE['basic_150']
    total_players_font = FONT_CACHE['basic_40']
    percentile_font = FONT_CACHE['basic_73']

    # Draw attribute name, rank, total players, and percentile texts
    ch.draw_centered_text(draw, attribute_name, attribute_name_font, fill=attribute_color, y_position=-13, x_center=150)
    ch.draw_centered_text(draw, str(rank), rank_font, y_position=50, x_center=110, fill=text_color)
    ch.draw_centered_text(draw, f'/ {total_players}', total_players_font, y_position=200, x_center=110, fill=text_color)
    if rank != 'N/A':
        ch.draw_centered_text(draw, str(percentile), percentile_font, y_position=155, x_center=249, fill=text_color)

    if attribute_rank_name in ['tot_rank', 'evo_rank', 'evd_rank', 'evs_rank', 'pkl_rank']:
        draw.rectangle([(15, 64), (284, 70)], fill=attribute_color)
        r = 9
        draw.ellipse([(18 - r, 67 - r), (18 + r, 67 + r)], fill=attribute_color)
        draw.ellipse([(281 - r, 67 - r), (281 + r, 67 + r)], fill=attribute_color)
    else:
        draw.rectangle([(10, 64), (290, 70)], fill=attribute_color)
    
    return ranking_section


def make_graph_section(player_row: pd.DataFrame, pos: str, mode: str = 'light') -> Image:
    """
    Creates the graph section Image for the player card. The rank section contains a graph that displays the some of player's attribute rankings 
    over multiple seasons.

    :param player_row: A Series containing player data
    :param pos: A str of the first letter of the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the graph section
    """

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        graph_background_color = constants.GRAPH_WHITE
        graph_text_color = constants.GRAPH_DARK

    else:
        background_color = constants.DARK
        graph_background_color = constants.GRAPH_DARK
        graph_text_color = constants.GRAPH_WHITE

    # Create graph component card
    graph_section_width = 1180
    graph_section_height = 650
    graph_section = Image.new("RGB", (graph_section_width, graph_section_height), color=background_color)

    # Define attributes top plot depending on the position
    if pos != 'G':
        attributes_to_plot = ['tot', 'evd', 'evo']
    else:
        attributes_to_plot = ['tot', 'evs', 'pkl']

    x_vals = list(range(len(attributes_to_plot)))

    # Store x-axis positions (fixed for 5 seasons)
    x_vals = list(range(1, 16, 3))

     # Create the figure with correct size
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(graph_section_width / 200, (graph_section_height - 50) / 200), facecolor=graph_background_color, dpi=200)

    # Get a list of the five seasons to plot
    seasons = [player_row['Season']]
    for _ in range(4):
        seasons.append(file.get_prev_season(seasons[-1]))
    seasons.reverse()

    # Iterate over attributes to plot
    for attribute_abbrev in attributes_to_plot:
        history_col = f"{attribute_abbrev}_history"

        history = player_row[history_col]

        # Convert string lists like to a real list
        if isinstance(history, str):
            history = ast.literal_eval(history)

        # Keep only valid values for plotting
        valid_data = [(x, y) for x, y in zip(x_vals, history) if y is not None and pd.notna(y)]
        if not valid_data:
            continue

        x_plot, y_plot = zip(*valid_data)

        # Plot overall line attribute
        if attribute_abbrev == 'tot':
            ax.plot(
                x_plot, y_plot,
                linewidth=5,
                linestyle='-',
                marker='o',
                markersize=9,
                color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_abbrev}_plot'),
                alpha=1
            )
        # Plot 5v5 attributes
        else:
            ax.plot(
                x_plot, y_plot,
                linewidth=3,
                linestyle='-',
                marker='o',
                markersize=6,
                color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_abbrev}_plot'),
                alpha=1
            )

    # X-axis settings
    ax.set_xticks(x_vals)
    ax.set_xticklabels(seasons, fontsize=15, fontweight='bold')
    ax.tick_params(axis='x', labelsize=9, length=0, colors=graph_text_color)
    ax.set_xlim(min(x_vals) - 1, max(x_vals) + 1)

    # Y-axis settings
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylim(-3, 103)
    ax.tick_params(axis='y', labelsize=15, labelcolor=constants.GRAPH_GRAY, length=0, pad=1)
    ax.set_yticklabels([0, 25, 50, 75, 100], fontsize=15, fontweight='bold', color=constants.GRAPH_GRAY)

    # Grid & Borders
    ax.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle="-", linewidth=2, color=constants.GRAPH_GRAY)
    ax.grid(axis='x', visible=False)
    ax.set_facecolor(graph_background_color)

    plt.tight_layout()

    # Convert plot to image
    graph_img = ch.plot_to_image(fig)
    graph_img = graph_img.resize((graph_section_width, graph_section_height - 50))
    graph_section.paste(graph_img, (0, 0))

    # Add player team image per season
    logo_x = 150
    team_history = ast.literal_eval(player_row['team_history'])
    for team in team_history:
        if team is None:
            logo_x += 220
            continue
        with open(f'data/assets/team_logos/{team}_{mode}.svg', 'rb') as f:
            svg_bytes = f.read()
        team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert("RGBA")
            
        # Calculate proportional height, resize and paste
        logo_width = 80
        w_percent = logo_width / team_logo.width
        logo_height = int(team_logo.height * w_percent)
        team_logo = team_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        graph_section.paste(team_logo, (logo_x, 575), team_logo)
        logo_x += 220

    plt.close(fig)

    return graph_section


def make_branding_section(team: str, mode: str = 'light') -> Image:
    """
    Creates the branding section Image for the player card. The branding section contains references to my website and socials, references to data sources,
    and and is stylized using the specified team's colors.

    :param team: A str representing the team abbreviation for the team to base the design color (e.g. 'TOR')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of branding section
    """

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        text_color = constants.DARK
        dividers_color = constants.SECONDARY_COLORS.get(team)
    else:
        background_color = constants.DARK
        text_color = constants.WHITE
        dividers_color = constants.WHITE
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    header_text_color = constants.WHITE
    header_shadow_color = constants.SECONDARY_COLORS.get(team)

    # Get updated date string
    update_date = constants.UPDATE_DATE

    # Create branding section card
    branding_section_width = 2000
    branding_section_height = 400
    branding_section = Image.new("RGB", (branding_section_width, branding_section_height), color=background_color)

    # Create draw image
    draw = ImageDraw.Draw(branding_section)

    # Get the font
    basic_font = FONT_CACHE['basic_73']
    
    # Branding text
    draw.text(xy=(100, 73), text='Website:', font=basic_font, fill=text_color)
    draw.text(xy=(100, 156), text='Socials:', font=basic_font, fill=text_color)

    ch.draw_righted_text(draw, 'analyticswithavery.com', basic_font, 73, 940, fill=text_color)
    ch.draw_righted_text(draw, 'analyticswavery', basic_font, 156, 940, fill=text_color)

    # Resources text
    draw.text(xy=(1060, 73), text='Player Data From:', font=basic_font, fill=text_color)
    draw.text(xy=(1060, 156), text='Date Updated:', font=basic_font, fill=text_color)

    ch.draw_righted_text(draw, 'nhl.com', basic_font, 73, 1900, fill=text_color)
    ch.draw_righted_text(draw, update_date, basic_font, 156, 1900, fill=text_color)
    
    # Get font
    heading_font = basic_font = FONT_CACHE['heading_116']

    # Draw rectangles
    draw.rectangle([(60, 0), (1940, 40)], fill=primary_team_color)
    draw.rectangle([(998, 80), (1002, 220)], fill=dividers_color)

    # Draw branding shape
    draw.polygon([(60, 260), (1940, 260), (1980, 380), (20, 380)], fill=primary_team_color)
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=268, x_center=996, fill=header_shadow_color)
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=264, x_center=1000, fill=header_text_color)

    return branding_section


def make_player_card(player_name: str, season: str, pos: str, mode: str='light', save: bool=True,) -> Image:
    """
    Generate and save a full player card image for a given player and season.

    The player card includes a header section, ranking section, stat graph section,
    and a branding section. The card is saved as a PNG image in a directory
    specific to the season.

    :param player_name: A str of the full name of the player (e.g. 'Auston Matthews')
    :param season: A str of the season that the data for the card comes from('YYYY-YYYY')
    :param pos: A str of the first letter of the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """

    # Get the player's current season data
    player_cur_season = ch.get_player_single_season(player_name, season, pos)

    # Get the player's team
    team = player_cur_season['Team']

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
    else:
        background_color = constants.DARK
    primary_team_color = constants.PRIMARY_COLORS.get(team)

    # Create player card
    card_width = 2000
    card_height = 2400
    player_card = Image.new('RGB', (card_width, card_height), color=background_color)

    # Add header section
    header_section = make_header_section(player_cur_season, mode)
    player_card.paste(header_section, (0, 0))

    # For skater cards
    if pos != 'G':
        # Add overall ranking
        tot_rank_section = make_rank_component(player_cur_season, 'tot_rank', mode)
        tot_rank_section = tot_rank_section.resize((512, 410), Image.Resampling.LANCZOS)
        player_card.paste(tot_rank_section, (742, 195))

        # Add main rankings
        evo_rank_section = make_rank_component(player_cur_season, 'evo_rank', mode)
        player_card.paste(evo_rank_section, (50, 750))

        evd_rank_section = make_rank_component(player_cur_season, 'evd_rank', mode)
        player_card.paste(evd_rank_section, (455, 750))

        ppl_rank_section = make_rank_component(player_cur_season, 'ppl_rank', mode)
        player_card.paste(ppl_rank_section, (50, 1050))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl_rank', mode)
        player_card.paste(pkl_rank_section, (455, 1050))

        # Add graph section
        graph_section = make_graph_section(player_cur_season, pos, mode)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add secondary rankings
        xgl_rank_section = make_rank_component(player_cur_season, 'xgl_rank', mode)
        player_card.paste(xgl_rank_section, (50, 1425))

        gol_rank_section = make_rank_component(player_cur_season, 'gol_rank', mode)
        player_card.paste(gol_rank_section, (50, 1715))

        fin_rank_section = make_rank_component(player_cur_season, 'fin_rank', mode)
        player_card.paste(fin_rank_section, (455, 1425))

        ast_rank_section = make_rank_component(player_cur_season, 'ast_rank', mode)
        player_card.paste(ast_rank_section, (455, 1715))

        pen_rank_section = make_rank_component(player_cur_season, 'pen_rank', mode) 
        player_card.paste(pen_rank_section, (850, 1425))

        hit_rank_section = make_rank_component(player_cur_season, 'hit_rank', mode)
        player_card.paste(hit_rank_section, (850, 1715))

        pdo_rank_section = make_rank_component(player_cur_season, 'pdo_rank', mode)
        player_card.paste(pdo_rank_section, (1245, 1425))

        ozs_rank_section = make_rank_component(player_cur_season, 'ozs_rank', mode)
        player_card.paste(ozs_rank_section, (1245, 1715))

        cmp_rank_section = make_rank_component(player_cur_season, 'cmp_rank', mode)
        player_card.paste(cmp_rank_section, (1640, 1425))

        tmt_rank_section = make_rank_component(player_cur_season, 'tmt_rank', mode)
        player_card.paste(tmt_rank_section, (1640, 1715))

    # For goalie cards
    else:
        # Add overall ranking
        tot_rank_section = make_rank_component(player_cur_season, 'tot_rank', mode)
        tot_rank_section = tot_rank_section.resize((512, 410), Image.Resampling.LANCZOS)
        player_card.paste(tot_rank_section, (742, 195))

        # Add main rankings
        evs_rank_section = make_rank_component(player_cur_season, 'evs_rank', mode)
        player_card.paste(evs_rank_section, (252, 750))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl_rank', mode)
        player_card.paste(pkl_rank_section, (252, 1050))

        # Add graph section
        graph_section = make_graph_section(player_cur_season, pos, mode)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add secondary rankings
        ldg_rank_section = make_rank_component(player_cur_season, 'ldg_rank', mode)
        player_card.paste(ldg_rank_section, (50, 1425))

        mdg_rank_section = make_rank_component(player_cur_season, 'mdg_rank', mode)
        player_card.paste(mdg_rank_section, (455, 1425))

        hdg_rank_section = make_rank_component(player_cur_season, 'hdg_rank', mode)
        player_card.paste(hdg_rank_section, (850, 1425))

        rbd_rank_section = make_rank_component(player_cur_season, 'rbd_rank', mode)
        player_card.paste(rbd_rank_section, (1245, 1425))

        tmd_rank_section = make_rank_component(player_cur_season, 'tmd_rank', mode)
        player_card.paste(tmd_rank_section, (1640, 1425))

        gre_rank_section = make_rank_component(player_cur_season, 'gre_rank', mode)
        player_card.paste(gre_rank_section, (50, 1715))

        qal_rank_section = make_rank_component(player_cur_season, 'qal_rank', mode)
        player_card.paste(qal_rank_section, (455, 1715))

        bad_rank_section = make_rank_component(player_cur_season, 'bad_rank', mode)
        player_card.paste(bad_rank_section, (850, 1715))

        awf_rank_section = make_rank_component(player_cur_season, 'awf_rank', mode)
        player_card.paste(awf_rank_section, (1245, 1715))

        dur_rank_section = make_rank_component(player_cur_season, 'dur_rank', mode)
        player_card.paste(dur_rank_section, (1640, 1715))

    # Add branding section
    branding_section = make_branding_section(team, mode)
    player_card.paste(branding_section, (0, 2000))

    if pos == 'F':
        pos_file = 'forwards' 
    elif pos == 'D':
        pos_file = 'defensemen'
    elif pos == 'G':
        pos_file = 'goalies'

    player_card = player_card.convert('RGB')

    file_name = f"{season}_{team}_{pos}_{player_name.replace(' ', '_')}_{mode}.png"

    if save:
        file.save_card(player_card, season, team, pos_file, file_name)

    print(f'========== {team} {pos} {player_name} ({mode}) card created for the {season} season! ==========')

    return player_card

