import pandas as pd
import streamlit as st
import matplotlib.colors as mcolors


rank_points_mapping = {
    1: 100,  2: 80,  3: 60,  4: 50,  5: 45,  6: 40,  7: 36,  8: 32,  9: 29, 10: 26,
   11: 24, 12: 22, 13: 20, 14: 18, 15: 16, 16: 15, 17: 14, 18: 13, 19: 12, 20: 11,
   21: 10, 22:  9, 23:  8, 24:  7, 25:  6, 26:  5, 27:  4, 28:  3, 29:  2, 30:  1
}

color_mapping_disciplines = {
    "Total Points": "#000000",
    "Slalom": "#4abaf7",
    "Downhill": "#e4e80c",
    "Giant Slalom": "#f525e0",
    "Super G": "#18f22e",

    "Overall Standings": "#ff7f0e",
    "10 km C": "#7f7f7f"

}

symbol_map = {
    'DH': 'circle',
    'SG': 'triangle-up',
    'GS': 'diamond',
    '10 km C': 'cross',
    'Overall Standings': 'square'
   
}


def count_results(df):

    # Count how many times the athlete has been in the top 10
    cnt_first_place = len(df[df["Position"] == 1])
    cnt_second_place = len(df[df["Position"] == 2])
    cnt_third_place = len(df[df["Position"] == 3])

    count_all = len(df)
    
    return [cnt_first_place, cnt_second_place, cnt_third_place], count_all

def transform_results(df, compare_on = False, FIS = False):

    if not compare_on:

        df = df.drop(columns=[
                            'Seasoncode',
                            'Description',
                            'Gender',
                            'Calstatuscode',
                            'Sectorcode',
                            'Competitorid',
                            'Competitorname',  
                            'Competitor_Nationcode',
                            'Fiscode',
                            'Level',
                            'Teamid',
                            'Disciplinename',
                            'Catname',
                            'Sectorcode',
                            'IsTeamResult',
                        ])
        
    else:

        df = df.drop(columns=[
                    'Seasoncode',
                    'Description',
                    'Gender',
                    'Calstatuscode',
                    'Sectorcode',
                    'Competitorid',  
                    'Competitor_Nationcode',
                    'Fiscode',
                    'Level',
                    'Teamid',
                    'Disciplinename',
                    'Catname',
                    'Sectorcode',
                    'IsTeamResult',
                ])
        
    if not FIS:

        df = df.drop(columns=['Catcode'])
    
    #Transform 0 to Null in Position
    df['Position'] = df['Position'].replace(0, None)

    #Transform QLF to Null in Status
    df['Status'] = df['Status'].replace("QLF", None)

    #Rename colum
    df = df.rename(columns={
                        "Raceid": "RaceID",
                        "WC_Points": "WC Points",
                        "Racepoints": "FIS Points",
                        "Details": "Racetime",
                        "Disciplinecode": "Discipline",
                        "Nationcode": "Country",
                    })

    return df

def get_card_metrics_WC(df, df_cards, season_select):

    df = df[df["Position"] != 0]

    count_Top3 = len(df[df["Position"] <= 3])
    count_Top10 = len(df[(df["Position"] <= 10) & (df["Position"] > 3)])
    count_Top30 = len(df[(df["Position"] <= 30) & (df["Position"] > 10)])

    df_cards = df_cards[df_cards["Position"] != 0]
    df_cards = df_cards[df_cards["Seasoncode"] == season_select-1]

    if df_cards.empty:
        return [count_Top3, count_Top10, count_Top30], [0, 0, 0]
    
    else:
        prev_count_Top3 = len(df_cards[df_cards["Position"] <= 3])
        prev_count_Top10 = len(df_cards[(df_cards["Position"] <= 10) & (df_cards["Position"] > 3)])
        prev_count_Top30 = len(df_cards[(df_cards["Position"] <= 30) & (df_cards["Position"] > 10)])

        return [count_Top3, count_Top10, count_Top30], [count_Top3-prev_count_Top3, count_Top10-prev_count_Top10, count_Top30-prev_count_Top30]

def highlight_positions(val):
    if pd.isna(val):  
        return 'background-color: rgba(0, 0, 0, 0)' 
    elif val <= 3:
        return 'background-color: rgba(0, 102, 255, 0.8)' 
    elif val > 3 and val <= 10:
        return 'background-color: rgba(102, 163, 255, 0.8)'
    elif val >= 11 and val <= 30:
        return 'background-color: rgba(204, 224, 255, 0.8)'
    return ''  # Default style

def highlight_status(val):
    if pd.isna(val):  
        return 'background-color: rgba(0, 0, 0, 0)' 
    elif "DNF" in val:
        return 'background-color: rgb(255, 153, 153); color: black'
    return ''  # Default style

def highlight_FIS_Points2(val):
    if pd.isna(val):  
        return 'background-color: rgba(0, 0, 0, 0)' 
    elif val <= 20:
        return 'background-color: rgba(0, 102, 255, 0.8)' 
    elif val > 20 and val <= 30:
        return 'background-color: rgba(102, 163, 255, 0.8)'
    elif val >= 30 and val <= 40:
        return 'background-color: rgba(204, 224, 255, 0.8)'
    return ''  # Default style


def highlight_FIS_Points(val, min_val, max_val):
    if pd.isna(val) or val == 0:  
        return 'background-color: rgba(0, 0, 0, 0)'  # Transparent for None/0 values

    max_val = max_val + (max_val*0.1) 

    # Normalize val to range between 0 and 1
    norm = (val - min_val) / (max_val - min_val) if max_val > min_val else 0
    
    # Define a colormap from light blue to white
    cmap = mcolors.LinearSegmentedColormap.from_list("blue_white", [(0/255, 102/255, 255/255), (1, 1, 1)])  # Light blue → White
    
    # Get the color from colormap
    rgba = cmap(norm)  # Returns (r, g, b, a) tuple

    # Convert to CSS rgba format, keeping alpha at 0.8
    return f'background-color: rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, 0.8)'




def get_top2_results(df, discipline, number):

    df_results = df.loc[df["Description"] == discipline].nsmallest(2, "Racepoints").reset_index(drop=True)
    length = len(df_results)

    df_results["Racedate"] = pd.to_datetime(df_results["Racedate"]).dt.strftime("%d.%m.%Y")

    if number == 1:
        if length >= 1:
            return df_results["Racepoints"][0], df_results["Place"][0], df_results["Racedate"][0]
        else:
            return -1, None, None

    elif number == 2:
        if length == 2:
            return df_results["Racepoints"][1], df_results["Place"][1], df_results["Racedate"][1]
        else:
            return -1, None, None

    else:
        st.error("Invalid number. Please choose 1 or 2.")



def get_numbers_LC(df):

    df = df[df["Catcode"] != "TRA"]

    races_total = len(df)
    dnf_total = len(df[df["Status"].str.contains("DNF", na=False)])
    dsq_total = len(df[df["Status"].str.contains("DSQ", na=False)])

    return races_total, dnf_total, dsq_total
        








