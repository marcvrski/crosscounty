import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math
import numpy as np
from streamlit_option_menu import option_menu

from services.database_utils import get_results_WC
from services.database_utils import get_seasons_LC, get_selected_data_LC, get_selection_options_LC

from services.data_functions import count_results, get_card_metrics_WC, transform_results, highlight_positions, highlight_status
from services.data_functions import rank_points_mapping, color_mapping_disciplines, symbol_map
from services.data_functions import get_top2_results, transform_results, get_numbers_LC
from services.data_functions import highlight_FIS_Points




### PAGE CONFIGURATION ###

st.set_page_config(
    page_title="Auswertungs-Dashboards",
    layout="wide",
    )

# Custom CSS for st.metrics
st.markdown(
    """
    <style>
        span[data-baseweb="tag"] {
            background-color: rgba(0, 104, 201, 0.5) !important;
            }
    </style>
    """,

    unsafe_allow_html=True
)


selected = option_menu(
            None, [ "Cross Country", "Lower Cup"],
            icons=["trophy-fill", "trophy"],
            orientation= "horizontal",
            styles={
                "container": {"padding": "0!important"},
                "icon": {"color": "rgb(0, 104, 201)", "font-size": "22px"},
                "nav-link": {"font-size": "22px", "text-align": "center", "margin":"0px",  "--hover-color": "#d6d6d6"},
                "nav-link-selected": {"background-color": "rgba(0, 104, 201, 0.5)", "font-weight": "normal", "color": "white"},
            })

#------------------------------------------------------------Cross Country------------------------------------------------------------
if selected == "Cross Country":

    ### INITIALIZE SESSION STATE ###

    if "results_LC" not in st.session_state:
        st.session_state.results_LC = None



    ### PAGE CONTENT ###

    st.title('Results Cross Country')

    df, athletes_unique, seasons_unique, description_unique = get_results_WC()

    compare_on = st.toggle("Compare Athletes")


    col1, col2, col3 = st.columns([1,1,2])

    with col1:
        season_select = st.selectbox(
            ':blue[Season]',
            seasons_unique,
        )

    with col2:
        if not compare_on:
            athlete_select = st.selectbox(
                ':blue[Athlete]',
                athletes_unique
            )
        else:
            athlete_select = st.multiselect(
                ':blue[Athlete]',
                athletes_unique,
                default=athletes_unique[0]
            )

    with col3:
        description_select = st.multiselect(
            ':blue[Discipline]',
            description_unique,
            default=description_unique
        )



    ### APPLY FILTERS FROM SELECTION ###

    if not compare_on:
        df = df[df["Competitorname"] == athlete_select]
        nation = df['Competitor_Nationcode'].unique().tolist()
        nation = nation[0]
    else:
        df = df[df["Competitorname"].isin(athlete_select)]


    df_cards = df.copy()
    df_cards = df_cards[df_cards["Description"].isin(description_select)]

    #Filter by season
    df = df[df["Seasoncode"] == season_select]

    #Add WC_Points to the dataframe
    df['WC_Points'] = df['Position'].map(rank_points_mapping).fillna(0).astype(int)

    #Create a copy for the barchart without discipline filter
    df_barchart = df.copy()

    #Filter by discipline
    df = df[df["Description"].isin(description_select)]

    #Order by Racedate
    df = df.sort_values(by='Racedate')

    #Create a copy for the lineplot without DNS and DNF
    df_lineplot = df[df["Position"] != 0]



    ### PAGE CONTENT ###
    if not compare_on:

        st.divider()
        st.subheader(f'Overview for {athlete_select} ({nation})')

        col2_1, col2_2, col2_3 = st.columns([3,3,1])

        with col2_1:
            chart_data = df_barchart.groupby("Description", as_index=False)["WC_Points"].sum()

            # Rename columns
            chart_data.columns = ["Discipline", "WC Points"]

            # Create an entry with discipline "Total Points" and sum of all WC_Points
            total_points = chart_data["WC Points"].sum()
            chart_data.loc[len(chart_data)] = ["Total Points", total_points]

            # Create colormapping for discipline bars
            chart_data["Color"] = chart_data["Discipline"].map(color_mapping_disciplines).fillna("gray")

            # Display bar chart with custom colors and text inside bars
            bars = px.bar(
                chart_data, 
                x="Discipline", 
                y="WC Points", 
                text_auto=True  # Display values inside bars
            )

            # Apply custom colors using `marker_color`
            bars.update_traces(marker=dict(color=chart_data["Color"], opacity=0.6), textposition='outside')

            bars.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=False
            )

            # Plot the bar chart
            st.plotly_chart(bars, use_container_width=True)

        with col2_2:
            # Get result counts
            counts, count_all = count_results(df)

            labels = ['Wins','Seconds','Thirds']
            values = counts
            colors = ['gold', 'silver', 'chocolate']

            # Create donut pie chart
            pie = go.Figure(data=[go.Pie(
                                    labels=labels, 
                                    values=values, 
                                    hole=.5, 
                                    marker=dict(colors=colors),
                                    textinfo="label+value"
                                )])

            pie.update_layout(
                height=400,
                annotations=[dict(
                        text= f'#{count_all} in Total', x=0.5 , y=0.5,
                        font_size=20, showarrow=False, xanchor="center"
                    )],
                legend=dict(
                        orientation="h",  #Puts legend in a row
                        yanchor="bottom", y=-0.1,  #Moves legend above plot
                        xanchor="center", x=0.5  #Centers legend
                    ),
                margin=dict(
                    l=20, r=20, t=50, b=20
                    )
            )

            #Plot the pie chart
            st.plotly_chart(pie, use_container_width=True)

        with col2_3:
            #Get card metrics
            card_metrics, diff_card_metrics = get_card_metrics_WC(df, df_cards, season_select)

            #Plot metrics
            st.metric("Finished in [1-3]", card_metrics[0], diff_card_metrics[0], border=True)
            st.metric("Finished in [4-10]", card_metrics[1], diff_card_metrics[1], border=True)
            st.metric("Finished in [11-30]", card_metrics[2], diff_card_metrics[2], border=True)

    st.divider()

    #Transform the results dataframe
    df = transform_results(df, compare_on = compare_on)

    #Apply custom styling to the dataframe highlighting positions and status
    styled_df = (df.style
                    .map(highlight_positions, subset=['Position'])
                    .map(highlight_status, subset=['Status']))

    if not compare_on:
        st.subheader(f'Results for {athlete_select}')

        #Change column order
        st.dataframe(styled_df, hide_index=True, use_container_width=True,
                        column_order=[
                            'RaceID',
                            'Racedate',
                            'Place',
                            'Country',
                            'Discipline',
                            'Webcomment',
                            'Bib',
                            'Position',
                            'Status',
                            'Racetime',
                            'WC Points',
                            'FIS Points'])
        
    else:
        st.subheader(f'Results for selected athletes')

        if len(athlete_select) != 0:
            #Change column order
            st.dataframe(styled_df, hide_index=True, use_container_width=True,
                        column_order=[
                            'RaceID',
                            'Racedate',
                            'Place',
                            'Country',
                            'Discipline',
                            'Competitorname',
                            'Webcomment',
                            'Bib',
                            'Position',
                            'Status',
                            'Racetime',
                            'WC Points',
                            'FIS Points'])
            
        else:
            st.warning("Please select at least one athlete to compare")


    # Create lineplot
    if len(athlete_select) != 0:
        # Create the plot
        if not compare_on:
            fig = px.line(df_lineplot, x='Racedate', y='Position', markers=True, text='Position')
        else:
            fig = px.line(df_lineplot, x='Racedate', y='Position', markers=True, text='Position', color='Competitorname')

        # Customize datapoints: use a constant symbol for every marker
        fig.update_traces(marker=dict(size=13, symbol="circle", color='black'))

        # Customize text labels
        fig.update_traces(textposition="bottom center", textfont=dict(size=15, color='black'))

        # Add Top 10 line
        fig.add_hline(y=10, line_dash="dash", line_color="black")

        # Ensure y-axis always covers the correct range
        max_position = df_lineplot['Position'].max() if (not math.isnan(df_lineplot['Position'].max())) else 0
        max_range = math.ceil(max_position / 10.0) * 10

        fig.update_yaxes(
            range=[max_range+11, 0], 
            tick0=5, dtick=5,  # Grid lines every 5 ranks  
            showgrid=True, gridcolor="lightgray", gridwidth=0.5  # Custom grid styling
        )

        # Format x-axis dates to DD-MM-YYYY
        fig.update_layout(
            xaxis=dict(tickformat="%d-%m-%Y")
        )

        # Customize hover appearance 
        fig.update_traces(
            customdata=df_lineplot[['Disciplinecode', 'Place']],
            hovertemplate="<b>Date:</b> %{x}<br>"  # Display Race Date
                        "<b>Position:</b> %{y}<br>"  # Display Position
                        "<b>Discipline:</b> %{customdata[0]}<br>"  # Show Discipline Code
                        "<b>Place:</b> %{customdata[1]}"  # Show Place
        )

        # Add customized legend with discipline symbols
        legend_traces = []

        for discipline, symbol in symbol_map.items():
            legend_traces.append(go.Scatter(
                x=[None],  # No actual x values (dummy trace)
                y=[None],  # No actual y values
                mode='markers',
                marker=dict(size=13, symbol=symbol, color='black'),
                name=discipline  # Legend label
            ))

        # Add the custom legend traces to the figure
        fig.add_traces(legend_traces)

        # Position the legend above the plot in a single line
        fig.update_layout(
            legend=dict(
                orientation="h",  # Horizontal legend
                yanchor="bottom", y=1.1,  # Place it above the plot
                xanchor="center", x=0.5  # Center-align the legend
            )
        )

        # Plot the line chart
        st.plotly_chart(fig, use_container_width=True)


#------------------------------------------------------------LOWER CUP------------------------------------------------------------
elif selected == "Lower Cup":

    ### PAGE CONFIGURATION ###

    # Custom CSS for st.metrics
    st.markdown(
        """
        <style>
        div[data-testid="stMetricValue"] {
            font-size: 22px !important;  /* Adjust font size */
        }
        div[data-testid="stMetricLabel"] {
            font-size: 16px !important;  /* Adjust label size */
        }
        span[data-baseweb="tag"] {
            background-color: rgba(0, 104, 201, 0.5) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    ### INITIALIZE SESSION STATE ###

    if "results_LC" not in st.session_state:
        st.session_state.results_LC = None



    ### PAGE CONTENT ###

    st.title('Results Alpine Skiing Lower Cup')

    compare_on = st.toggle("Compare Athletes")
    swiss_only_on = st.toggle("Show only swiss races")

    # Load data unique seasons and athletes
    seasons_unique_LC = get_seasons_LC()

    col1, col2, col3, col4 = st.columns([1,1,1,1])

    with col1:
        season_select_LC = st.selectbox(
            ':blue[Season]',
            seasons_unique_LC,
            )
        # Get the selection options based on the selected season
        df = get_selection_options_LC(season_select_LC)

    with col2:
        if not compare_on:
            gender_select_LC = st.selectbox(
                ':blue[Gender]',
                ["M", "W"],
            )
            # Adjust further selection options
            df = df[df["Gender"] == gender_select_LC]

        else:
            gender_select_LC = st.multiselect(
                ':blue[Gender]',
                ["M", "W"],
                default="M"
            )
            # Adjust further selection options
            df = df[df["Gender"].isin(gender_select_LC)]

    with col3:
        if not compare_on:
            nation_select_LC = st.selectbox(
                ':blue[Nation (Athlete)]',
                df['Competitor_Nationcode'].unique().tolist(),
            )
            # Adjust further selection options
            df = df[df["Competitor_Nationcode"] == nation_select_LC]

        else:
            nation_select_LC = st.multiselect(
                ':blue[Nation (Athlete)]',
                df['Competitor_Nationcode'].unique().tolist(),
                default="SUI"
            )
            # Adjust further selection options
            df = df[df["Competitor_Nationcode"].isin(nation_select_LC)]

    with col4:
        if not compare_on:
            athlete_select_LC = st.selectbox(
                ':blue[Athletes]',
                df['Competitorname'].unique().tolist(),
            )

        else:
            athlete_select_LC = st.multiselect(
                ':blue[Athletes]',
                df['Competitorname'].unique().tolist(),
                default=df['Competitorname'].unique().tolist()[0]
            )



    ### LOAD & FILTER DATA ###
    if not compare_on:
        st.session_state.results_LC, nation, categories_unique, disciplines_unique = get_selected_data_LC(season_select_LC, athlete_select_LC)
    else:
        st.session_state.results_LC, nation, categories_unique, disciplines_unique = get_selected_data_LC(season_select_LC, tuple(athlete_select_LC), compare_on)

    if swiss_only_on:
        st.session_state.results_LC = st.session_state.results_LC[st.session_state.results_LC["Nationcode"] == "SUI"]



    ### PAGE CONTENT ###

    if not st.session_state.results_LC.empty and st.session_state.results_LC is not None:

        col2_1, col2_2 = st.columns([1,1])

        with col2_1:
            categories_select_LC = st.multiselect(
                ':blue[Categories]',
                categories_unique,
                default=categories_unique
            )
        
        with col2_2:
            disciplines_select_LC = st.multiselect(
                ':blue[Disciplines]',
                disciplines_unique,
                default=disciplines_unique
            )

        if not compare_on:

            st.divider()
            st.subheader(f'Overview for {athlete_select_LC} ({nation})')

            col3_1, col3_2 = st.columns([1,1])

            with col3_1:
                df_prep = st.session_state.results_LC.copy()

                def avg_best_two(group):
                    # Select the smallest two values and compute mean
                    return group.nsmallest(2).mean()  

                # Group by 'Disciplines' and apply the function
                chart_data = df_prep.groupby("Description")["Racepoints"].apply(avg_best_two).reset_index()

                # Rename columns
                chart_data.columns = ["Discipline", "AVG Points"]

                # Create colormapping for discipline bars
                chart_data["Color"] = chart_data["Discipline"].map(color_mapping_disciplines).fillna("gray")

                # Display bar chart with custom colors and text inside bars
                bars = px.bar(
                    chart_data, 
                    x="Discipline", 
                    y="AVG Points", 
                    text_auto=True  # Display values inside bars
                )

                # Apply custom colors using `marker_color`
                bars.update_traces(marker=dict(color=chart_data["Color"], opacity=0.6), textposition='outside')

                bars.update_layout(
                    height=500,
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False 
                )

                # Plot the bar chart
                st.plotly_chart(bars, use_container_width=True)

            with col3_2:
                # Get result counts
                cnt_total, cnt_dnf, cnt_dsq = get_numbers_LC(st.session_state.results_LC)

                col4_1, col4_2, col4_3 = st.columns([1,1,1])

                with col4_1:
                    st.metric(
                            f"Total races",
                            f"{cnt_total}",
                            border=True
                        )

                with col4_2:
                    st.metric(
                            f"Total races DNF",
                            f"{cnt_dnf}",
                            border=True
                        )

                with col4_3:
                    st.metric(
                            f"Total Races DSQ",
                            f"{cnt_dsq}",
                            border=True
                        )

                col5_1, col5_2 = st.columns([1,1])

                with col5_1:
                    if "Slalom" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Slalom", 1)
                        st.metric(
                            f"Best Slalom: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Giant Slalom" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Giant Slalom", 1)
                        st.metric(
                            f"Best Giant Slalom: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Super G" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Super G", 1)
                        st.metric(
                            f"Best Super G: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Downhill" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Downhill", 1)
                        st.metric(
                            f"Best Downhill: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Alpine Combined" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Alpine Combined", 1)
                        st.metric(
                            f"Best Alpine Combined: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )

                with col5_2:
                    if "Slalom" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Slalom", 2)
                        st.metric(
                            f"2nd. Best Slalom: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Giant Slalom" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Giant Slalom", 2)
                        st.metric(
                            f"2nd. Best Giant Slalom: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Super G" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Super G", 2)
                        st.metric(
                            f"2nd. Best Super G: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Downhill" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Downhill", 2)
                        st.metric(
                            f"2nd. Best Downhill: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )
                    if "Alpine Combined" in disciplines_select_LC:
                        pts, loc, dat = get_top2_results(st.session_state.results_LC, "Alpine Combined", 2)
                        st.metric(
                            f"2nd. Alpine Combined: ({loc})",
                            f"{pts} pts. ({dat})" if pts >= 0 else "No points",
                            border=True
                        )

        # Filtering the table
        df_table = st.session_state.results_LC.copy()
        df_table = df_table[df_table["Description"].isin(disciplines_select_LC)]
        df_table = df_table[df_table["Catcode"].isin(categories_select_LC)]
        df_table = df_table.sort_values(by='Racedate')

        #Transform the results dataframe
        df_table = transform_results(df_table, compare_on = compare_on, FIS = True)

        #Apply custom styling to the dataframe highlighting positions and status
        min_fis = df_table["FIS Points"].replace(0, np.nan).min() 
        max_fis = df_table["FIS Points"].max()

        styled_df = (df_table.style
                    .map(lambda x: highlight_FIS_Points(x, min_fis, max_fis), subset=['FIS Points'])
                    .map(highlight_status, subset=['Status'])
                    .format({"FIS Points": "{:.2f}"}))

        st.divider()

        if not compare_on:
            st.subheader(f'Results for {athlete_select_LC}') 

            #Change column order
            st.dataframe(styled_df, hide_index=True, use_container_width=True,
                            column_order=[
                                'RaceID',
                                'Racedate',
                                'Place',
                                'Country',
                                'Catcode',
                                'Discipline',
                                'Webcomment',
                                'Bib',
                                'Position',
                                'FIS Points',
                                'Status',
                                'Racetime'])

        else:
            st.subheader(f'Results for selected athletes')

            if len(athlete_select_LC) != 0:
                #Change column order
                st.dataframe(styled_df, hide_index=True, use_container_width=True,
                            column_order=[
                                'RaceID',
                                'Racedate',
                                'Place',
                                'Country',
                                'Catcode',
                                'Discipline',
                                'Competitorname',
                                'Webcomment',
                                'Bib',
                                'Position',
                                'FIS Points',
                                'Status',
                                'Racetime'])
                
            else:
                st.warning("Please select at least one athlete to compare")

        # Create lineplot
        if len(athlete_select_LC) != 0:

            df_lineplot = st.session_state.results_LC.copy()
            df_lineplot = df_lineplot.sort_values(by='Racedate')
            df_lineplot = df_lineplot.dropna(subset=['Racepoints'])

            # Create a new column 'Symbol' by mapping 'Disciplinecode' to symbols
            df_lineplot['Symbol'] = df_lineplot['Disciplinecode'].map(symbol_map)

            # Create the plot
            if not compare_on:
                fig = px.line(df_lineplot, x='Racedate', y='Racepoints', markers=True, text='Racepoints')
            else:
                fig = px.line(df_lineplot, x='Racedate', y='Racepoints', markers=True, text='Racepoints', color='Competitorname')

            # Customize datapoints
            fig.update_traces(marker=dict(size=13, symbol=df_lineplot['Symbol'], color='black'))

            # Customize text labels
            fig.update_traces(textposition="bottom center", textfont=dict(size=15, color='black'))

            # Ensure y-axis always covers the correct range
            max_position = df_lineplot['Racepoints'].max() if (not math.isnan(df_lineplot['Racepoints'].max())) else 0
            max_range = math.ceil(max_position / 10.0) * 10

            fig.update_yaxes(
                title_text="FIS Points",    # Rename y-axis to 'FIS Points'
                range=[max_range+11, 0], 
                tick0=5, dtick=5,  # Grid lines every 5 ranks  
                showgrid=True, gridcolor="lightgray", gridwidth=0.5  # Custom grid styling
            )

            # Format x-axis dates to DD-MM-YYYY
            fig.update_layout(
                xaxis=dict(tickformat="%d-%m-%Y")
            )

            # Customize hover appearance 
            fig.update_traces(
                customdata=df_lineplot[['Disciplinecode', 'Place']],
                hovertemplate="<b>Date:</b> %{x}<br>"  # Display Race Date
                            "<b>FIS Points:</b> %{y}<br>"  # Display Position
                            "<b>Discipline:</b> %{customdata[0]}<br>"  # Show Discipline Code
                            "<b>Place:</b> %{customdata[1]}"  # Show Place
            )

            # Add customized legend with discipline symbols
            legend_traces = []

            for discipline, symbol in symbol_map.items():
                legend_traces.append(go.Scatter(
                    x=[None],  # No actual x values (dummy trace)
                    y=[None],  # No actual y values
                    mode='markers',
                    marker=dict(size=13, symbol=symbol, color='black'),
                    name=discipline  # Legend label
                ))

            # Add the custom legend traces to the figure
            fig.add_traces(legend_traces)

            # Position the legend above the plot in a single line
            fig.update_layout(
                legend=dict(
                    orientation="h",  # Horizontal legend
                    yanchor="bottom", y=1.1,  # Place it above the plot
                    xanchor="center", x=0.5  # Center-align the legend
                )
            )

            # Plot the line chart
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("No data available for this selection.")
