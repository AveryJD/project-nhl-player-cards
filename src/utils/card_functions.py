# ====================================================================================================
# FUNCTIONS FOR PLAYER CARD CREATION
# ====================================================================================================

# Imports
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import os
from utils import card_data as cd
from utils import card_helpers as ch
from utils import card_images as ci
from utils import constants

DATA_DIR = constants.DATA_DIR


def make_header_section(player_row: pd.Series, custom_team='NONE') -> Image:
    """
    ADD DOCSTRING
    
    """

    # Get banner variables
    name = player_row['Player']
    season = player_row['Season']
    if custom_team == 'NONE':
        team = player_row['Team']
    else:
        team = custom_team
    team_full_name = constants.TEAM_NAMES.get(team)
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    secondary_team_color = constants.SECONDARY_COLORS.get(team)

    # Get profile variables
    position = player_row['Position']
    age = player_row['Age']
    birth_date = ch.get_word_date(player_row['Date of Birth'])
    height = f"{int(player_row['Height (in)']) // 12}\'{int(player_row['Height (in)']) % 12}\""
    weight = f"{player_row['Weight (lbs)']} lbs"
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
    role = cd.get_player_role(player_row)
    games_played = player_row['GP']
    if position == 'G':
        save_percentage = format(player_row['SV%'], '.3f')
        goals_against_avg = format(player_row['GAA'], '.2f')
    else:
        goals = player_row['Goals']
        assists = player_row['Total Assists']
        points = player_row['Total Points']

    # Get contract variables
    cap_hit = '-.---'                   # TEMPORARY
    contract_years_left = '-'           # TEMPORARY
    expiry_status = '-FA'               # TEMPORARY

    # Create header section card
    header_section_width = 2000
    header_section_height = 700
    header_section = Image.new("RGB", (header_section_width, header_section_height), color=(255, 255, 255))

    # Create draw object
    draw = ImageDraw.Draw(header_section)
    
    # Get player team logo
    team_img = ci.get_team_image(team)
    team_img = team_img.resize((560, 560))
    header_section.paste(team_img, (70, 140), team_img)

    if position == 'G':
        pos = 'g'
    elif position == 'D':
        pos = 'd'
    else:
        pos = 'f'


    # Get player image
    player_img = ci.get_player_image(name, team, season, pos)
    player_img = player_img.resize((500, 500))
    header_section.paste(player_img, (100, 160), player_img)

    # Load fonts
    basic_font_path = f'{DATA_DIR}/assets/fonts/basic.ttf'
    heading_font_path = f'{DATA_DIR}/assets/fonts/header.ttf'
    basic_font = ImageFont.truetype(basic_font_path, 40)
    basic_subheading_font = ImageFont.truetype(basic_font_path, 70)
    heading_font = ImageFont.truetype(heading_font_path, 116)
    subheading_font = ImageFont.truetype(heading_font_path, 58)
    
    # Draw subheaders text
    ch.draw_centered_text(draw, 'PROFILE', font=basic_subheading_font, y_position=180, x_center=1000)
    ch.draw_centered_text(draw, 'CONTRACT', font=basic_subheading_font, y_position=180, x_center=1650)
    ch.draw_centered_text(draw, 'STATS', font=basic_subheading_font, y_position=420, x_center=1650)

    # Draw profile segment text
    draw.text(xy=(680, 270), text='POSITION:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 310), text='AGE:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 350), text='DATE OF BIRTH:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 390), text='HEIGHT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 430), text='WEIGHT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 470), text='DRAFT YEAR:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 510), text='DRAFT POSITION:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(680, 550), text='NATIONALITY:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, text=position, font=basic_font, y_position=270, x_right=1320)
    ch.draw_righted_text(draw, text=age, font=basic_font, y_position=310, x_right=1320)
    ch.draw_righted_text(draw, text=birth_date, font=basic_font, y_position=350, x_right=1320)
    ch.draw_righted_text(draw, text=height, font=basic_font, y_position=390, x_right=1320)
    ch.draw_righted_text(draw, text=weight, font=basic_font, y_position=430, x_right=1320)
    ch.draw_righted_text(draw, text=draft_year, font=basic_font, y_position=470, x_right=1320)
    ch.draw_righted_text(draw, text=draft_position, font=basic_font, y_position=510, x_right=1320)
    ch.draw_righted_text(draw, text=nationality, font=basic_font, y_position=550, x_right=1320)

    # Draw salary segment text
    draw.text(xy=(1400, 270), text='CAP HIT:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(1400, 310), text='YEARS REMAINING:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(1400, 350), text='EXPIRY STATUS:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, text=f'${cap_hit} M', font=basic_font, y_position=270, x_right=1900)
    ch.draw_righted_text(draw, text=contract_years_left, font=basic_font, y_position=310, x_right=1900)
    ch.draw_righted_text(draw, text=expiry_status, font=basic_font, y_position=350, x_right=1900)

    # Draw stats segment text
    if position == 'G':
        draw.text(xy=(1400, 510), text='ROLE:', font=basic_font, fill=(0,0,0))
        draw.text(xy=(1400, 550), text='GP-SV%-GAA:', font=basic_font, fill=(0,0,0))

        ch.draw_righted_text(draw, text=role, font=basic_font, y_position=510, x_right=1900)
        ch.draw_righted_text(draw, text=f'{games_played}-{save_percentage}-{goals_against_avg}', font=basic_font, y_position=550, x_right=1900)
    
    else:
        draw.text(xy=(1400, 510), text='ROLE:', font=basic_font, fill=(0,0,0))
        draw.text(xy=(1400, 550), text='GP-G-A-P:', font=basic_font, fill=(0,0,0))

        ch.draw_righted_text(draw, text=role, font=basic_font, y_position=510, x_right=1900)
        ch.draw_righted_text(draw, text=f'{games_played}-{goals}-{assists}-{points}', font=basic_font, y_position=550, x_right=1900)
    

    # Draw banner shape
    draw.polygon([(20, 20), (1980, 20), (1940, 140), (60, 140)], fill=primary_team_color)
    # Draw name, team, and season drop shadow
    draw.text(xy=(76, 28), text=name, font=heading_font, fill=secondary_team_color)
    ch.draw_righted_text(draw, season, subheading_font, 28, 1916, fill=secondary_team_color)
    ch.draw_righted_text(draw, team_full_name, subheading_font, 78, 1916, fill=secondary_team_color)
    # Draw name and season text
    draw.text(xy=(80, 22), text=name, font=heading_font, fill=(255,255,255))
    ch.draw_righted_text(draw, season, subheading_font, 24, 1920, fill=(255, 255, 255))
    ch.draw_righted_text(draw, team_full_name, subheading_font, 74, 1920, fill=(255, 255, 255))

    # Draw bottom rectangle
    draw.rectangle([(60, 660), (1940, 700)], fill=primary_team_color)

    # Draw divider rectangles
    draw.rectangle([(638, 200), (644, 600)], fill=secondary_team_color)
    draw.rectangle([(1356, 200), (1362, 600)], fill=secondary_team_color)
    draw.rectangle([(1400, 402), (1900, 408)], fill=secondary_team_color)

    return header_section


# ORGANIZE CODE BETTER
def make_rank_component(player_row: pd.Series, attribute_rank_name: str) -> Image:
    """
    ADD DOCSTRING AND ORGANIZE CODE BETTER
    
    """

    # Create ranking component card
    ranking_section_width = 300
    ranking_section_height = 240
    ranking_section = Image.new("RGB", (ranking_section_width, ranking_section_height), color=(255, 255, 255))

    # Create draw object 
    draw = ImageDraw.Draw(ranking_section)


    # Get attribute name text and color
    attribute_name = constants.ATRIBUTE_NAMES.get(attribute_rank_name)
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

    total_players = player_row[f'{attribute_abrev}_players']

    rank, percentile = cd.get_rank_and_percentile(player_row, attribute_rank_name, total_players)
        
    # Get percentile color
    if rank == 'N/A':
        percentile_color = (150 / 255, 150 / 255, 150 / 255)
    else:
        percentile_color = cd.get_percentile_color(percentile)
    
    # Create the percentile bar
    fig, ax = plt.subplots(figsize=(5, 10))
    ax.bar(x=[0], height=percentile, width=50, color=percentile_color)
    
    
    # Remove ticks
    ax.set_yticks([])
    ax.set_xticks([1])
    ax.tick_params(bottom=False)

    ax.set_xticklabels([percentile])
    
    # Make border around percentile bar
    ax.set_xlim(0, 25)  
    ax.set_ylim(0, 100)
    ax.spines['left'].set_position(('data', 0))
    ax.spines['right'].set_position(('data', 25))
    ax.spines['top'].set_position(('data', 100))
    ax.spines['bottom'].set_position(('data', 0))
    ax.spines['left'].set_color('lightgrey')
    ax.spines['right'].set_color('lightgrey')
    ax.spines['top'].set_color('lightgrey')
    ax.spines['bottom'].set_color('lightgrey')
    ax.spines['left'].set_linewidth(15)
    ax.spines['right'].set_linewidth(15)
    ax.spines['top'].set_linewidth(15)
    ax.spines['bottom'].set_linewidth(15)

    # Add percentile bar to ranking section card
    percentile_bar = ch.plot_to_image(fig)
    percentile_bar = percentile_bar.resize((100, 200))
    ranking_section.paste(percentile_bar, (200, 60))

    # Load fonts
    basic_font_path = f'{DATA_DIR}/assets/fonts/basic.ttf'
    attribute_name_font = ImageFont.truetype(basic_font_path, 60)
    rank_font = ImageFont.truetype(basic_font_path, 160)
    total_players_font = ImageFont.truetype(basic_font_path, 40)
    percentile_font = ImageFont.truetype(basic_font_path, 50)

    # Draw attribute name, rank, total players, and percentile texts
    ch.draw_centered_text(draw, attribute_name, attribute_name_font, y_position=0, x_center=150)
    ch.draw_centered_text(draw, str(rank), rank_font, y_position=40, x_center=110)
    if rank != 'N/A':
        ch.draw_centered_text(draw, f'/ {total_players}', total_players_font, y_position=200, x_center=110)
        ch.draw_centered_text(draw, str(percentile), percentile_font, y_position=174, x_center=250)
    
    draw.rectangle([(10, 64), (290, 70)], fill=attribute_color)

    plt.close()
    
    return ranking_section


def make_ranking_section(player_cur_season: pd.Series, pos) -> Image:
    """
    ADD DOCSTRING
    
    """

    ranking_section_width = 2000
    ranking_section_height = 620
    ranking_section = Image.new("RGB", (ranking_section_width, ranking_section_height), color=(255, 255, 255))

    if pos == 'g':
        evd_rank_section = make_rank_component(player_cur_season, 'ldg_rank')
        ranking_section.paste(evd_rank_section, (455, 310))

        pkl_rank_section = make_rank_component(player_cur_season, 'mdg_rank')
        ranking_section.paste(pkl_rank_section, (850, 310))

        phy_rank_section = make_rank_component(player_cur_season, 'hdg_rank')
        ranking_section.paste(phy_rank_section, (1245, 310))


        sht_rank_section = make_rank_component(player_cur_season, 'pkl_rank')
        ranking_section.paste(sht_rank_section, (1245, 20))

        ppl_rank_section = make_rank_component(player_cur_season, 'evs_rank')
        ranking_section.paste(ppl_rank_section, (850, 20))

        evo_rank_section = make_rank_component(player_cur_season, 'all_rank')
        ranking_section.paste(evo_rank_section, (455, 20))


    else:
        # Add skater attribute ranking sections

        ppl_rank_section = make_rank_component(player_cur_season, 'ppl_rank')
        ranking_section.paste(ppl_rank_section, (60, 20))

        pkl_rank_section = make_rank_component(player_cur_season, 'pkl_rank')
        ranking_section.paste(pkl_rank_section, (60, 310))

    
        evo_rank_section = make_rank_component(player_cur_season, 'evo_rank')
        ranking_section.paste(evo_rank_section, (455, 20))

        evd_rank_section = make_rank_component(player_cur_season, 'evd_rank')
        ranking_section.paste(evd_rank_section, (455, 310))
        

        off_rank_section = make_rank_component(player_cur_season, 'off_rank')
        ranking_section.paste(off_rank_section, (850, 20))

        def_rank_section = make_rank_component(player_cur_season, 'def_rank')
        ranking_section.paste(def_rank_section, (850, 310))


        sht_rank_section = make_rank_component(player_cur_season, 'sht_rank')
        ranking_section.paste(sht_rank_section, (1245, 20))

        plm_rank_section = make_rank_component(player_cur_season, 'plm_rank')
        ranking_section.paste(plm_rank_section, (1245, 310))



        phy_rank_section = make_rank_component(player_cur_season, 'phy_rank')
        ranking_section.paste(phy_rank_section, (1640, 20))

        pen_rank_section = make_rank_component(player_cur_season, 'pen_rank')
        ranking_section.paste(pen_rank_section, (1640, 310))


    return ranking_section


def make_graph_section(player_multiple_seasons: pd.DataFrame, pos: str) -> Image:
    """
    Creates a PIL Image of a graph displaying multiple percentiles over multiple seasons for specified attributes.

    :param player_multiple_seasons: a DataFrame of a player's multiple seasons of stats
    :param attributes_to_plot: a list of attribute names to plot
    :return: a PIL Image of the graph section
    """

    # Create graph component card
    graph_section_width = 2000
    graph_section_height = 1300
    graph_section = Image.new("RGB", (graph_section_width, graph_section_height), color=(255, 255, 255))

    if pos == 'g':
        attributes_to_plot = ['pkl', 'evs', 'all', 'ldg', 'mdg', 'hdg']
    else:
        attributes_to_plot = ['def','off', 'pen', 'phy', 'plm', 'sht']

    # Make a list with the current season
    cur_season = max(player_multiple_seasons['Season'])
    
    # Add the previous four seasons to the list and put the oldest season first
    seasons = [cur_season]
    for _ in range(4):
        seasons.append(cd.get_prev_season(seasons[-1]))
    seasons.reverse()

    # Store x-axis positions (fixed for 5 seasons)
    x_vals = list(range(1, 16, 3))  # Ensures a 5-season timeline

    plt.style.use('default')
    # Create the figure with correct size
    fig, ax = plt.subplots(figsize=(2000 / 200, 1280 / 200), dpi=200)

    # Iterate over attributes
    for attribute_name in attributes_to_plot:
        percentiles = []
        for season in seasons:
            if season in player_multiple_seasons['Season'].values:
                cur_player_row = player_multiple_seasons[player_multiple_seasons['Season'] == season].iloc[0]
                total_players = player_multiple_seasons.loc[player_multiple_seasons['Season'] == season, 'all_players'].iloc[0]

                if total_players:
                    rank, percentile = cd.get_rank_and_percentile(cur_player_row, f"{attribute_name}_rank", total_players)
                    if rank != 'N/A':
                        percentiles.append(percentile)
                else:
                    percentiles.append(None)
            else:
                percentiles.append(None) 


        # Plot lines
        dashed_line_attributes = ['sht', 'plm', 'phy', 'pen', 'ldg', 'mdg', 'hdg']

        valid_data = [(x, y) for x, y in zip(x_vals, percentiles) if y is not None]
        if valid_data:
            if attribute_name in dashed_line_attributes:
                x_plot, y_plot = zip(*valid_data)
                ax.plot(x_plot, y_plot, linewidth=1.5, linestyle='--', marker='o', markersize=6, color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_name}_plot'), alpha=1)
            else:
                x_plot, y_plot = zip(*valid_data)
                ax.plot(x_plot, y_plot, linewidth=5, linestyle='-', marker='o', markersize=10, color=constants.PLOT_ATTRIBUTE_COLORS.get(f'{attribute_name}_plot'), alpha=1)
    

    # X-axis settings
    ax.set_xticks(x_vals)
    ax.set_xticklabels(seasons, fontsize=15, fontweight='bold')
    ax.tick_params(axis='x', labelsize=12, length=7, direction='inout')
    ax.set_xlim(min(x_vals) - 1, max(x_vals) + 1)

    # Y-axis settings
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylim(-2, 102)
    ax.tick_params(axis='y', labelsize=10, labelcolor='black', length=0, pad=-1)

    # Grid & Borders
    ax.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle="-", linewidth=2, color='lightgrey')
    ax.grid(axis='x', visible=False)


    # Convert plot to image
    graph_img = ch.plot_to_image(fig)
    graph_img = graph_img.resize((2200, 1430))
    graph_section.paste(graph_img, (-125, -110))

    plt.close(fig)

    return graph_section


def make_branding_section(team: str) -> Image:
    """
    ADD DOCSTRING
    
    """

    # Create branding section card
    branding_section_width = 2000
    branding_section_height = 400
    branding_section = Image.new("RGB", (branding_section_width, branding_section_height), color=(255, 255, 255))

    # Create draw image
    draw = ImageDraw.Draw(branding_section)

    # Get the font
    basic_font_path = f'{DATA_DIR}/assets/fonts/basic.ttf'
    basic_font = ImageFont.truetype(basic_font_path, 55)
    
    # Branding text
    draw.text(xy=(100, 73), text='Website:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(100, 156), text='Socials:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, 'analyticswithavery.com', basic_font, 73, 940)
    ch.draw_righted_text(draw, 'Analytics With Avery', basic_font, 156, 940)

    
    # Resources text
    draw.text(xy=(1060, 73), text='Player Data From:', font=basic_font, fill=(0,0,0))
    draw.text(xy=(1060, 156), text='Cap Data From:', font=basic_font, fill=(0,0,0))

    ch.draw_righted_text(draw, 'NaturalStatTrick.com', basic_font, 73, 1900)
    ch.draw_righted_text(draw, 'Coming Soon', basic_font, 156, 1900)
    
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    secondary_team_color = constants.SECONDARY_COLORS.get(team)
    heading_font_path = f'{DATA_DIR}/assets/fonts/header.ttf'
    heading_font = ImageFont.truetype(heading_font_path, 116)

    draw.rectangle([(60, 0), (1940, 40)], fill=primary_team_color)

    draw.rectangle([(998, 80), (1002, 220)], fill=secondary_team_color)

    draw.polygon([(60, 260), (1940, 260), (1980, 380), (20, 380)], fill=primary_team_color)
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=268, x_center=996, fill=(0, 0, 0))
    ch.draw_centered_text(draw, 'Analytics With Avery', font=heading_font, y_position=264, x_center=1000, fill=(255, 255, 255))

    return branding_section



# ====================================================================================================
# WHOLE CARD CREATION FUNCTIONS
# ====================================================================================================

def make_player_card(player_name: str, season: str, pos: str, custom_team='NONE') -> None:
    """
    ADD DOCSTRING
    
    """

    # Get the data for a player's five seasons
    player_five_seasons = cd.get_player_multiple_seasons(player_name, season, pos,)

    # Get the player's current season data
    player_cur_season = player_five_seasons.iloc[0]

    # Get the player's header information
    player_header_row = cd.get_player_header_row(player_name, season, pos)

    if custom_team == 'NONE':
        team = player_cur_season['Team']
    else:
        team = custom_team

    # Create player card
    card_width = 2000
    card_height = 3000
    player_card = Image.new('RGB', (card_width, card_height), color=(255, 255, 255))

    # Add header section
    header_section = make_header_section(player_header_row, custom_team)
    player_card.paste(header_section, (0, 0))

    # Add ranking section
    ranking_section = make_ranking_section(player_cur_season, pos)
    player_card.paste(ranking_section, (0, 700))

    # Add graph section
    graph_section = make_graph_section(player_five_seasons, pos)
    player_card.paste(graph_section, (0, 1320))

    # Add branding section
    branding_section = make_branding_section(team)
    player_card.paste(branding_section, (0, 2600))


    draw = ImageDraw.Draw(player_card)
    primary_team_color = constants.PRIMARY_COLORS.get(team)
    draw.rectangle([(60, 1280), (1940, 1320)], fill=primary_team_color)


    # Save card as a PNG in the proper folder (create it if it doesnt exist)
    save_dir = os.path.join(DATA_DIR, 'cards', season,)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{team}_{pos.upper()}_{player_name.replace(' ', '_')}_{season}.png")
    player_card = player_card.convert('RGB')
    player_card.save(save_path, 'PNG')

    print(f'{player_name} card created')


