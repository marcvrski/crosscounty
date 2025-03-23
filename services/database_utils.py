import streamlit as st
import pandas as pd

from google.oauth2 import service_account
from google.cloud import bigquery

    
'''def load_datapool(query):
    
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gbq_service_account"])
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    query_job = client.query(query)
    rows_raw = query_job.result()
    rows = [dict(row) for row in rows_raw]
    return pd.DataFrame(rows)

'''

### WORLD CUP ###

@st.cache_data(ttl='4h', show_spinner='Fetching new data...')
def get_results_WC():

    query = """ 
    SELECT * FROM `swissski-production.raw_fis.fis_results` 
    WHERE Sectorcode = 'CC' 
    AND Seasoncode >= 2023
    AND Status != 'DNS'
    """

    """
    SELECT * FROM `swissski-production.raw_fis.fis_results` 
    WHERE Sectorcode = 'AL' 
    AND Catcode = 'WC'
    AND Seasoncode >= 2014
    AND Description IN ('Downhill', 'Slalom', 'Super G', 'Giant Slalom')
    AND Status != 'DNS'
    """

    #df = load_datapool(query)

    
    try:
        df = pd.read_csv("results_cc.csv")
    except FileNotFoundError:
        df = load_datapool(query)
        df.to_csv("results_cc.csv", index=False)

    df_athletes_sorted = df.copy()

    # Sort by lowest position and highest season
    df_athletes_sorted['Position'] = pd.to_numeric(df_athletes_sorted['Position'], errors='coerce')
    df_athletes_sorted['Seasoncode'] = pd.to_numeric(df_athletes_sorted['Seasoncode'], errors='coerce')
    df_athletes_sorted = df_athletes_sorted.sort_values(by=['Position', 'Seasoncode'], ascending=[True, False])


    athletes_unique = df_athletes_sorted['Competitorname'].unique().tolist()
    seasons_unique = df['Seasoncode'].unique().tolist()
    descriptions_unique = df['Description'].unique().tolist()

    seasons_unique = sorted(seasons_unique, reverse=True)

    return df, athletes_unique, seasons_unique, descriptions_unique



### LOWER CUP ###

@st.cache_data(ttl='4h', show_spinner='Fetching new data...')
def get_selected_data_LC(season, athlete, compare_on=False):

    if not compare_on:
        query = f"""
        SELECT * FROM `swissski-production.raw_fis.fis_results` 
        WHERE Sectorcode = 'AL' 
        AND Catcode != 'WC'
        AND Seasoncode = {season}
        AND Competitorname = '{athlete}'
        AND Status != 'DNS'
        """

        df = load_datapool(query)
        
        if not df.empty:
            df = df[df['Description'].isin(['Downhill', 'Slalom', 'Super G', 'Giant Slalom', 'Alpine Combined'])]
            df["Racepoints"] = pd.to_numeric(df["Racepoints"], errors="coerce")
            
            nation = df['Competitor_Nationcode'].unique().tolist()
            nation = nation[0]

            categories_unique = df['Catcode'].unique().tolist()
            disciplines_unique = df['Description'].unique().tolist()

            return df, nation, categories_unique, disciplines_unique
        
    else:
        query = f"""
        SELECT * FROM `swissski-production.raw_fis.fis_results` 
        WHERE Sectorcode = 'AL' 
        AND Catcode != 'WC'
        AND Seasoncode = {season}
        AND Status != 'DNS'
        AND Competitorname IN ({', '.join(f"'{name}'" for name in athlete)})
        """

        df = load_datapool(query)

        if not df.empty:
            df = df[df['Description'].isin(['Downhill', 'Slalom', 'Super G', 'Giant Slalom', 'Alpine Combined'])]
            df["Racepoints"] = pd.to_numeric(df["Racepoints"], errors="coerce")

            categories_unique = df['Catcode'].unique().tolist()
            disciplines_unique = df['Description'].unique().tolist()

        return df, "SUI", categories_unique, disciplines_unique

    return df, None, None, None


@st.cache_data(ttl='4h', show_spinner='Fetching new data...')
def get_selection_options_LC(season):
    
    query = f"""
    SELECT Competitorname, Competitor_Nationcode, Gender
    FROM `swissski-production.raw_fis.fis_results`
    WHERE Sectorcode = 'AL'
    AND Catcode != 'WC'
    AND Seasoncode = {season}
    AND Description IN ('Downhill', 'Slalom', 'Super G', 'Giant Slalom', 'Alpine Combined')
    AND Status != 'DNS'
    GROUP BY Competitorname, Competitor_Nationcode, Gender;
    """

    df = load_datapool(query)

    return df


@st.cache_data(ttl='4h', show_spinner='Fetching new data...')
def get_seasons_LC():

    query_seasons = """
    SELECT DISTINCT Seasoncode FROM `swissski-production.raw_fis.fis_results` 
    WHERE Sectorcode = 'AL' 
    AND Seasoncode >= 2014
    """

    df_seasons = load_datapool(query_seasons)

    seasons_unique = df_seasons['Seasoncode'].unique().tolist()
    seasons_unique_sorted = sorted(seasons_unique, reverse=True)

    return seasons_unique_sorted