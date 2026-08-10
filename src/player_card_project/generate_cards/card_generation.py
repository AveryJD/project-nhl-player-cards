# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD GENERATION
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
from player_card_project.generate_cards import card_utils as ch
from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR

# Load and cache fonts
BASIC_FONT_PATH = constants.BASIC_FONT_PATH
HEADING_FONT_PATH = constants.HEADING_FONT_PATH

FONT_CACHE = {
    'basic_40': ImageFont.truetype(BASIC_FONT_PATH, 40),
    'basic_60': ImageFont.truetype(BASIC_FONT_PATH, 60),
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
    position_name = constants.POSITION_NAMES.get(specific_position)
    shoots_catches = player_row.get('Shoots Catches')
    handedness = constants.HANDEDNESS_NAMES.get(shoots_catches)
    if position != 'G':
        position_str = f'{position_name} ({handedness} Shot)'
    else:
        position_str = f'{position_name} (Catches {handedness})'
    role = player_row['Role']
    age = int(player_row['Age'])
    birth_date = ch.get_word_date(player_row['Date of Birth'])
    age_str = f'{age} ({birth_date})'
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
        xgoals = str(player_row['ixG'])
        xgoals_for_percent = format((player_row['xGF%'] / 100), '.3f')
    else:
        record = f"{player_row['W']}-{player_row['L']}-{player_row['OT/SO']}"
        save_percentage = str(float(player_row['SV%']))
        gsax = format(player_row['xG Against'] - player_row['Goals Against'], '.2f')

    # Create header section card
    header_section_width = 2000
    header_section_height = 700
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=background_color)

    # Create draw object
    draw = ImageDraw.Draw(header_section)
    
    # Load fonts
    basic_font = FONT_CACHE['basic_60']
    heading_font = FONT_CACHE['heading_116']

    # x center for team logo and player headshot
    left_center_x = 362

    with open(f'{DATA_DIR}/assets/team_logos/{team}_{mode}.svg', 'rb') as f:
        svg_bytes = f.read()
    team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert("RGBA")
    logo_width = 808
    w_percent = logo_width / team_logo.width
    logo_height = int(team_logo.height * w_percent)
    team_logo = team_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    header_section.paste(team_logo, (left_center_x - logo_width // 2, 140), team_logo)

    headshot_size = 520
    headshot_img = ch.get_player_headshot(season, team, player_id)
    headshot_img = headshot_img.resize((headshot_size, headshot_size))
    # Crop transparent bottom padding then paste bottom-aligned so jerseys line up with header bottom bar
    bbox = headshot_img.getbbox()
    if bbox:
        headshot_img = headshot_img.crop((0, 0, headshot_img.width, bbox[3]))
    paste_y = 660 - headshot_img.height
    header_section.paste(headshot_img, (left_center_x - headshot_size // 2, paste_y), headshot_img)

    # Row y positions
    row_ys = [165, 222, 279, 336, 395, 450, 507, 564]
    x_right = 1500
    x_val   = 1550

    ch.draw_righted_text(draw, text='Position:', font=basic_font, y_position=row_ys[0], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Role:',     font=basic_font, y_position=row_ys[1], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Age:',      font=basic_font, y_position=row_ys[2], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Size:',   font=basic_font, y_position=row_ys[3], x_right=x_right, fill=text_color)
    ch.draw_righted_text(draw, text='Games:',   font=basic_font, y_position=row_ys[4], x_right=x_right, fill=text_color)

    draw.text(xy=(x_val, row_ys[0]), text=position_str,  font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[2]), text=age_str,   font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[3]), text=size_str,         font=basic_font, fill=text_color)
    draw.text(xy=(x_val, row_ys[4]), text=games_played_str, font=basic_font, fill=text_color)

    if position != 'G':
        ch.draw_righted_text(draw, text='G-A-P:',  font=basic_font, y_position=row_ys[5], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='xG:',     font=basic_font, y_position=row_ys[6], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='5v5 xGF%:',  font=basic_font, y_position=row_ys[7], x_right=x_right, fill=text_color)
        draw.text(xy=(x_val, row_ys[1]), text=f'{role} ({toi_formatted})', font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[5]), text=stat_line,          font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[6]), text=xgoals,             font=basic_font, fill=text_color)
        draw.text(xy=(x_val, row_ys[7]), text=xgoals_for_percent, font=basic_font, fill=text_color)
    else:
        ch.draw_righted_text(draw, text='W-L-OTL:', font=basic_font, y_position=row_ys[5], x_right=x_right, fill=text_color)
        ch.draw_righted_text(draw, text='Save%:',  font=basic_font, y_position=row_ys[6], x_right=x_right, fill=text_color)
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


def make_rank_component(player_row: pd.Series, attribute_key: str, mode: str = 'light') -> Image:
    """
    Creates a ranking component for a specific player attribute, displaying the player's rank, total players, 
    percentile, and a visual percentile bar.

    :param player_row: A Series containing player data
    :param attribute_key: A str representing the attribute key that is being ranked (e.g. 'ovr')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: An Image of the rank component
    """

    # Get attribute name
    attribute_name = constants.ATTRIBUTE_NAMES.get(attribute_key)

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        text_color = constants.DARK
        if attribute_key in ['ovr', 'evo', 'evd', 'evs'] or (player_row['Position'] == 'G' and attribute_key == 'pkl'):
            attribute_color = constants.ATTRIBUTE_COLORS[attribute_name]
        else:
            attribute_color = constants.DARK
    else:
        background_color = constants.DARK
        text_color = constants.WHITE
        if attribute_key in ['ovr', 'evo', 'evd', 'evs'] or (player_row['Position'] == 'G' and attribute_key == 'pkl'):
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
    if attribute_key == 'ppl':
        total_players_key = 'ppl'
    elif attribute_key == 'pkl' and player_row.get('Position') != 'G':
        total_players_key = 'pkl'
    else:
        total_players_key = 'all'

    # Get total players
    total_players = int(player_row[f'{total_players_key}_players'])

    # Get rank and percentile
    rank, percentile = ch.get_rank_and_percentile(player_row, attribute_key)
        
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
        ch.draw_centered_text(draw, str(percentile), percentile_font, y_position=155, x_center=253, fill=text_color, stroke_width=3, stroke_fill=background_color)

    if attribute_key in ['ovr', 'evo', 'evd', 'evs'] or (player_row['Position'] == 'G' and attribute_key == 'pkl'):
        draw.rectangle([(15, 64), (284, 70)], fill=attribute_color)
        r = 9
        draw.ellipse([(18 - r, 67 - r), (18 + r, 67 + r)], fill=attribute_color)
        draw.ellipse([(281 - r, 67 - r), (281 + r, 67 + r)], fill=attribute_color)
    else:
        draw.rectangle([(10, 64), (290, 70)], fill=attribute_color)
    
    return ranking_section


def make_graph_section(player_row: pd.DataFrame, position: str, mode: str = 'light') -> Image:
    """
    Creates the graph section Image for the player card. The rank section contains a graph that displays the some of player's attribute rankings 
    over multiple seasons.

    :param player_row: A Series containing player data
    :param position: A str representing the player's position ('F', 'D', or 'G')
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
    if position != 'G':
        attributes_to_plot = ['ovr', 'evd', 'evo']
    else:
        attributes_to_plot = ['ovr', 'evs', 'pkl']

    x_vals = list(range(len(attributes_to_plot)))

    # Store x-axis positions (fixed for 5 seasons)
    x_vals = list(range(1, 16, 3))

     # Create the figure with correct size
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(graph_section_width / 200, (graph_section_height - 50) / 200), facecolor=graph_background_color, dpi=200)

    # Get a list of the five seasons to plot
    seasons = [player_row['Season']]
    for _ in range(4):
        seasons.append(data_io.get_prev_season(seasons[-1]))
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
        if attribute_abbrev == 'ovr':
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
        with open(f'{DATA_DIR}/assets/team_logos/{team}_{mode}.svg', 'rb') as f:
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
    draw.text(xy=(100, 68), text='Website:', font=basic_font, fill=text_color)
    draw.text(xy=(100, 145), text='Socials:', font=basic_font, fill=text_color)

    ch.draw_righted_text(draw, 'analyticswithavery.com', basic_font, 68, 940, fill=text_color)
    ch.draw_righted_text(draw, 'analyticswavery', basic_font, 145, 940, fill=text_color)

    # Resources text
    draw.text(xy=(1060, 68), text='Data and Images Sourced From:', font=basic_font, fill=text_color)
    draw.text(xy=(1060, 145), text='Date Updated:', font=basic_font, fill=text_color)

    ch.draw_righted_text(draw, 'NHL', basic_font, 68, 1900, fill=text_color)
    ch.draw_righted_text(draw, update_date, basic_font, 145, 1900, fill=text_color)
    
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


def make_player_card(player_name: str, season: str, position: str, mode: str='light', save: bool=True,) -> Image:
    """
    Generate and save a full player card image for a given player and season.

    The player card includes a header section, ranking section, stat graph section,
    and a branding section. The card is saved as a PNG image in a directory
    specific to the season.

    :param player_name: A str of the full name of the player (e.g. 'Auston Matthews')
    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :return: None
    """

    # Get the player's current season data
    player_cur_season = ch.get_player_single_season(player_name, season, position)

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
    if position != 'G':
        # Add overall ranking
        tot_rank_section = make_rank_component(player_cur_season, 'ovr', mode)
        tot_rank_section = tot_rank_section.resize((512, 410), Image.Resampling.LANCZOS)
        player_card.paste(tot_rank_section, (742, 195))

        # Add main rankings
        evo_rank_section = make_rank_component(player_cur_season, 'evo', mode)
        player_card.paste(evo_rank_section, (50, 750))

        evd_rank_section = make_rank_component(player_cur_season, 'evd', mode)
        player_card.paste(evd_rank_section, (455, 750))

        ppl_rank_section = make_rank_component(player_cur_season, 'ppl', mode)
        player_card.paste(ppl_rank_section, (50, 1050))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl', mode)
        player_card.paste(pkl_rank_section, (455, 1050))

        # Add graph section
        graph_section = make_graph_section(player_cur_season, position, mode)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add secondary rankings
        xgl_rank_section = make_rank_component(player_cur_season, 'xgl', mode)
        player_card.paste(xgl_rank_section, (50, 1425))

        gol_rank_section = make_rank_component(player_cur_season, 'fin', mode)
        player_card.paste(gol_rank_section, (455, 1425))

        fin_rank_section = make_rank_component(player_cur_season, 'pen', mode)
        player_card.paste(fin_rank_section, (850, 1425))

        ast_rank_section = make_rank_component(player_cur_season, 'tmt', mode)
        player_card.paste(ast_rank_section, (1245, 1425))

        pen_rank_section = make_rank_component(player_cur_season, 'cmp', mode) 
        player_card.paste(pen_rank_section, (1640, 1425))

        hit_rank_section = make_rank_component(player_cur_season, 'gol', mode)
        player_card.paste(hit_rank_section, (50, 1715))

        pdo_rank_section = make_rank_component(player_cur_season, 'ast', mode)
        player_card.paste(pdo_rank_section, (455, 1715))

        ozs_rank_section = make_rank_component(player_cur_season, 'hit', mode)
        player_card.paste(ozs_rank_section, (850, 1715))

        cmp_rank_section = make_rank_component(player_cur_season, 'ozs', mode)
        player_card.paste(cmp_rank_section, (1245, 1715))

        tmt_rank_section = make_rank_component(player_cur_season, 'pdo', mode)
        player_card.paste(tmt_rank_section, (1640, 1715))

    # For goalie cards
    else:
        # Add overall ranking
        tot_rank_section = make_rank_component(player_cur_season, 'ovr', mode)
        tot_rank_section = tot_rank_section.resize((512, 410), Image.Resampling.LANCZOS)
        player_card.paste(tot_rank_section, (742, 195))

        # Add main rankings
        evs_rank_section = make_rank_component(player_cur_season, 'evs', mode)
        player_card.paste(evs_rank_section, (252, 750))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl', mode)
        player_card.paste(pkl_rank_section, (252, 1050))

        # Add graph section
        graph_section = make_graph_section(player_cur_season, position, mode)
        player_card.paste(graph_section, (800, 700))

        # Draw divider rectangle
        draw = ImageDraw.Draw(player_card)
        draw.rectangle([(60, 1340), (1940, 1380)], fill=primary_team_color)

        # Add secondary rankings
        ldg_rank_section = make_rank_component(player_cur_season, 'ldg', mode)
        player_card.paste(ldg_rank_section, (50, 1425))

        mdg_rank_section = make_rank_component(player_cur_season, 'mdg', mode)
        player_card.paste(mdg_rank_section, (455, 1425))

        hdg_rank_section = make_rank_component(player_cur_season, 'hdg', mode)
        player_card.paste(hdg_rank_section, (850, 1425))

        rbd_rank_section = make_rank_component(player_cur_season, 'rbd', mode)
        player_card.paste(rbd_rank_section, (1245, 1425))

        tmd_rank_section = make_rank_component(player_cur_season, 'tmd', mode)
        player_card.paste(tmd_rank_section, (1640, 1425))

        gre_rank_section = make_rank_component(player_cur_season, 'gre', mode)
        player_card.paste(gre_rank_section, (50, 1715))

        qal_rank_section = make_rank_component(player_cur_season, 'qal', mode)
        player_card.paste(qal_rank_section, (455, 1715))

        bad_rank_section = make_rank_component(player_cur_season, 'bad', mode)
        player_card.paste(bad_rank_section, (850, 1715))

        awf_rank_section = make_rank_component(player_cur_season, 'awf', mode)
        player_card.paste(awf_rank_section, (1245, 1715))

        wrk_rank_section = make_rank_component(player_cur_season, 'wrk', mode)
        player_card.paste(wrk_rank_section, (1640, 1715))

    # Add branding section
    branding_section = make_branding_section(team, mode)
    player_card.paste(branding_section, (0, 2000))

    pos_file = constants.POSITION_FOLDERS[position]

    player_card = player_card.convert('RGB')

    file_name = f"{season}_{team}_{position}_{player_name.replace(' ', '_')}_{mode}.png"

    if save:
        data_io.save_card(player_card, season, team, pos_file, file_name)

    print(f'========== {team} {position} {player_name} ({mode}) card created for the {season} season! ==========')

    return player_card















def make_mini_player_card(player_name: str, season: str, position: str, mode: str='light', save: bool=True, special_teams: str=None) -> Image:
    """
    Generate and save a mini player card image for a given player and season.

    The player card includes a header section and a ranking section, and a branding section.
    The card is saved as a PNG image in a directory specific to the season.

    :param player_name: A str of the full name of the player (e.g. 'Auston Matthews')
    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the player's position ('F', 'D', or 'G')
    :param mode: A str determining the style of card ('light' or 'dark')
    :param special_teams: An optional str ('PP' or 'PK') to show a special-teams focused card.
                          'PP' shows 5v5 Offense + Power Play. 'PK' shows 5v5 Defense + Penalty Kill.
                          Default is None (shows all four skater rank sections as normal).
    :return: None
    """

    # Get the player's current season data
    player_row = ch.get_player_single_season(player_name, season, position)

    # Get the player's team
    team = player_row['Team']

    # Load fonts
    heading_font = FONT_CACHE['heading_70']

    # Get color variables
    if mode == 'light':
        background_color = constants.WHITE
        text_color = constants.DARK
        secondary_team_color = constants.SECONDARY_COLORS.get(team)
    else:
        background_color = constants.DARK
        text_color = constants.WHITE
        secondary_team_color = constants.WHITE
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    header_text_color = constants.WHITE
    header_shadow_color = constants.SECONDARY_COLORS.get(team)

    # Create player card
    card_width = 1000
    card_height = 1100
    mini_player_card = Image.new('RGB', (card_width, card_height), color=background_color)

    draw = ImageDraw.Draw(mini_player_card)

    # Get banner variables
    header_name = player_name
    for symbol, replacement in constants.SYMBOLS_TO_REPLACE.items():
        header_name = header_name.replace(symbol, replacement)
    season = player_row['Season']

    # Get profile variables
    player_id = player_row['Player ID']
    position = player_row['Position']
    
    # Get team logo
    with open(f'{DATA_DIR}/assets/team_logos/{team}_{mode}.svg', 'rb') as f:
        svg_bytes = f.read()
    team_logo = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_bytes))).convert("RGBA")

    # Calculate proportional height, resize and paste
    logo_width = 600
    w_percent = logo_width / team_logo.width
    logo_height = int(team_logo.height * w_percent)
    team_logo = team_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    mini_player_card.paste(team_logo, (-30, 100), team_logo)

    # Get player image and paste
    headshot_img = ch.get_player_headshot(season, team, player_id)
    headshot_img = headshot_img.resize((400, 400))
    mini_player_card.paste(headshot_img, (80, 100), headshot_img)

    # Draw Overall rank component scaled and centred in the right section (x=500–1000, y=100–500).
    # make_rank_component's native size is 300x240 (5:4) -- same ratio as this 500x400 budget, so
    # 450x360 (90% scale) fits with a clean margin and no distortion.
    overall_rank_name = 'ovr_rank'
    overall_section = make_rank_component(player_row, overall_rank_name, mode)
    overall_w, overall_h = 450, 360
    overall_section = overall_section.resize((overall_w, overall_h), Image.Resampling.LANCZOS)
    overall_x = 500 + (500 - overall_w) // 2   # centred in right half
    overall_y = 100 + (400 - overall_h) // 2   # centred between banner and bottom bar
    mini_player_card.paste(overall_section, (overall_x, overall_y))

    # Draw banner
    draw.polygon([(20, 20), (980, 20), (940, 100), (60, 100)], fill=primary_team_color)

    # Draw name drop shadow then name text
    draw.text(xy=(76, 28), text=header_name, font=heading_font, fill=header_shadow_color)
    draw.text(xy=(80, 24), text=header_name, font=heading_font, fill=header_text_color)

    # Draw bottom rectangle
    draw.rectangle([(60, 500), (940, 540)], fill=primary_team_color)

    # Every rank section below is pasted at ROW_SIZE (312x250, same 5:4 aspect ratio as
    # make_rank_component's actual native size of 300x240) instead of native size, so two rows fit
    # between the bottom rectangle (y=540) and the card's bottom border without distortion.
    ROW_SIZE = (312, 250)
    # Column x-positions center each column on the same x's the full card's columns are centered on.
    LEFT_COL_X = 300 - ROW_SIZE[0] // 2
    RIGHT_COL_X = 700 - ROW_SIZE[0] // 2
    GOALIE_LEFT_COL_X = 200 - ROW_SIZE[0] // 2

    def _paste_row(attribute_key, xy):
        section = make_rank_component(player_row, attribute_key, mode)
        section = section.resize(ROW_SIZE, Image.Resampling.LANCZOS)
        mini_player_card.paste(section, xy)

    # Second grid row sits ROW_SIZE[1] + a 30px gap below the first
    ROW2_Y = 550 + ROW_SIZE[1] + 30

    # For skater cards
    if position != 'G':
        if special_teams == 'PP':
            # 5v5 Offense + Power Play side by side, vertically centred in ranking area
            y_st = 540 + (card_height - 540 - ROW_SIZE[1]) // 2
            _paste_row('evo_rank', (LEFT_COL_X, y_st))
            _paste_row('ppl_rank', (RIGHT_COL_X, y_st))
        elif special_teams == 'PK':
            # 5v5 Defense + Penalty Kill side by side, vertically centred in ranking area
            y_st = 540 + (card_height - 540 - ROW_SIZE[1]) // 2
            _paste_row('evd_rank', (LEFT_COL_X, y_st))
            _paste_row('pkl_rank', (RIGHT_COL_X, y_st))
        else:
            # Default: all four rankings in two rows
            _paste_row('evo_rank', (LEFT_COL_X, 550))
            _paste_row('evd_rank', (RIGHT_COL_X, 550))
            _paste_row('ppl_rank', (LEFT_COL_X, ROW2_Y))
            _paste_row('pkl_rank', (RIGHT_COL_X, ROW2_Y))

    # For goalie cards
    else:
        # Overall rank centered on the same x the full card centers its Overall badge on
        _paste_row('ovr_rank', (500 - ROW_SIZE[0] // 2, 550))
        _paste_row('evs_rank', (GOALIE_LEFT_COL_X, ROW2_Y))
        _paste_row('pkl_rank', (RIGHT_COL_X, ROW2_Y))

    pos_file = constants.POSITION_FOLDERS[position]

    mini_player_card = mini_player_card.convert('RGB')

    # Draw mode-aware border
    border_color = constants.WHITE if mode == 'dark' else constants.DARK
    draw_border = ImageDraw.Draw(mini_player_card)
    draw_border.rectangle([(0, 0), (card_width - 1, card_height - 1)], outline=border_color, width=8)

    file_name = f"{season}_mini_{team}_{position}_{player_name.replace(' ', '_')}_{mode}.png"

    if save:
        data_io.save_card(mini_player_card, season, team, pos_file, file_name)
        print(f'========== {team} {position} {player_name} ({mode}) mini card created for the {season} season! ==========')

    return mini_player_card



def make_lineup_card(team: str, season: str, players: dict, mode: str = 'light', save: bool = True) -> Image.Image:
    """
    Generate a lineup card for a team by arranging mini player cards on a single image.

    Sections (top to bottom): forwards (4 lines × 3 cols), defensemen (3 pairs × 2 cols),
    goalies (1 row × 2 cols), extras (1 row, centred), injured (1 row, centred).

    :param team: A str of the team abbreviation (e.g. 'TOR')
    :param season: A str representing the season ('YYYY-YYYY')
    :param players: A dict mapping player names to a (position, slot) tuple, where position is 'F', 'D', or 'G'
                    and slot is e.g. '1LW', '2LD', '1G', 'Extra', or 'Injured'
                    e.g. {'Sidney Crosby': ('F', '1C'), 'Kris Letang': ('D', '1LD'),
                          'Tristan Jarry': ('G', '1G'), 'Evgeni Malkin': ('F', 'Injured')}
    :param mode: A str determining the style of card ('light' or 'dark')
    :param save: A bool determining whether to save the card
    :return: A PIL Image of the lineup card
    """

    # ── Layout constants ────────────────────────────────────────────────────────
    card_w, card_h = 1000, 1200
    padding     = 60   # left/right canvas margin
    h_gap       = 40   # horizontal gap between cards
    row_gap     = 30   # vertical gap between rows within a section
    col_gap     = 200  # horizontal gap between forward column and defense/goalie column
    def_gol_gap = 30   # vertical gap between defense rows and goalie row (same as row_gap)
    big_gap     = 150  # gap before extras and between extras and injured
    banner_h    = 160  # height reserved for top polygon banner
    branding_h  = 120  # height reserved for bottom polygon branding

    # Canonical slot order
    FORWARD_SLOTS = ['1LW', '1C', '1RW', '2LW', '2C', '2RW', '3LW', '3C', '3RW', '4LW', '4C', '4RW']
    DEFENSE_SLOTS = ['1LD', '1RD', '2LD', '2RD', '3LD', '3RD']
    GOALIE_SLOTS  = ['1G', '2G']

    # ── Group players by section ─────────────────────────────────────────────────
    forwards = {}  # slot -> (name, position)
    defense  = {}  # slot -> (name, position)
    goalies  = {}  # slot -> (name, position)
    extras   = []  # [(name, position)]
    injured  = []  # [(name, position)]

    for name, (position, slot) in players.items():
        if slot == 'Extra':
            extras.append((name, position))
        elif slot == 'Injured':
            injured.append((name, position))
        elif position == 'F':
            forwards[slot] = (name, position)
        elif position == 'D':
            defense[slot] = (name, position)
        elif position == 'G':
            goalies[slot] = (name, position)

    # ── Generate mini cards ──────────────────────────────────────────────────────
    def gen(name, position):
        return make_mini_player_card(name, season, position, mode=mode, save=False)

    fwd_cards  = {slot: gen(name, position) for slot, (name, position) in forwards.items()}
    def_cards  = {slot: gen(name, position) for slot, (name, position) in defense.items()}
    gol_cards  = {slot: gen(name, position) for slot, (name, position) in goalies.items()}
    ext_cards  = [gen(name, position) for name, position in extras]
    inj_cards  = [gen(name, position) for name, position in injured]

    # ── Canvas dimensions ────────────────────────────────────────────────────────
    # Layout: forwards (left) | defense + goalies + injured (right)
    #         extras sit below the forwards on the left
    left_w  = 3 * card_w + 2 * h_gap   # 3-column forward section
    right_w = 2 * card_w + h_gap        # 2-column defense/goalie section
    canvas_w = padding + left_w + col_gap + right_w + padding

    fwd_h = 4 * card_h + 3 * row_gap
    def_h = 3 * card_h + 2 * row_gap

    left_content_h  = fwd_h + ((big_gap + card_h) if ext_cards  else 0)
    right_content_h = def_h + def_gol_gap + card_h + ((big_gap + card_h) if inj_cards else 0)
    content_h = max(left_content_h, right_content_h)

    canvas_h = banner_h + content_h + big_gap + branding_h

    # ── Colors ───────────────────────────────────────────────────────────────────
    background_color  = constants.WHITE if mode == 'light' else constants.DARK
    primary_color     = constants.PRIMARY_COLORS.get(team)
    shadow_color      = constants.SECONDARY_COLORS.get(team)
    header_text_color = constants.WHITE

    # ── Create canvas ────────────────────────────────────────────────────────────
    lineup_card = Image.new('RGB', (canvas_w, canvas_h), color=background_color)
    draw = ImageDraw.Draw(lineup_card)

    heading_font = FONT_CACHE['heading_70']

    # ── Column x positions ───────────────────────────────────────────────────────
    fwd_xs       = [padding + i * (card_w + h_gap) for i in range(3)]
    right_x      = padding + left_w + col_gap   # x where right section starts
    def_xs       = [right_x + i * (card_w + h_gap) for i in range(2)]
    gol_xs       = def_xs  # goalies share the same 2-column x positions

    y_content = banner_h  # top of content area (same for both sides)

    # ── Paste forward cards (4 rows × 3 cols, left) ─────────────────────────────
    for idx, slot in enumerate(FORWARD_SLOTS):
        row, col = divmod(idx, 3)
        if slot in fwd_cards:
            lineup_card.paste(fwd_cards[slot], (fwd_xs[col], y_content + row * (card_h + row_gap)))

    # ── Paste extra cards below forwards (1 row, left, centred) ─────────────────
    if ext_cards:
        y_ext = y_content + fwd_h + big_gap
        ext_total_w = len(ext_cards) * card_w + (len(ext_cards) - 1) * h_gap
        ext_x_start = padding + (left_w - ext_total_w) // 2
        for i, card in enumerate(ext_cards):
            lineup_card.paste(card, (ext_x_start + i * (card_w + h_gap), y_ext))

    # ── Paste defense cards (3 rows × 2 cols, right) ────────────────────────────
    for idx, slot in enumerate(DEFENSE_SLOTS):
        row, col = divmod(idx, 2)
        if slot in def_cards:
            lineup_card.paste(def_cards[slot], (def_xs[col], y_content + row * (card_h + row_gap)))

    # ── Paste goalie cards below defense (1 row × 2 cols, right) ────────────────
    y_gol = y_content + def_h + def_gol_gap
    for idx, slot in enumerate(GOALIE_SLOTS):
        if slot in gol_cards:
            lineup_card.paste(gol_cards[slot], (gol_xs[idx], y_gol))

    # ── Paste injured cards below goalies (1 row, right, centred) ────────────────
    if inj_cards:
        y_inj = y_gol + card_h + big_gap
        inj_total_w = len(inj_cards) * card_w + (len(inj_cards) - 1) * h_gap
        inj_x_start = right_x + (right_w - inj_total_w) // 2
        for i, card in enumerate(inj_cards):
            lineup_card.paste(card, (inj_x_start + i * (card_w + h_gap), y_inj))

    # ── Save and return ──────────────────────────────────────────────────────────
    lineup_card = lineup_card.convert('RGB')
    file_name = f"{season}_lineup_{team}_{mode}.png"
    if save:
        data_io.save_card(lineup_card, season, team, 'lineup', file_name)

    print(f'========== {team} lineup card created for the {season} season! ==========')

    return lineup_card