import streamlit as st
import datetime as dt
import time

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.dates as mdates
from dateutil.relativedelta import relativedelta

from scipy import stats
import numpy as np
import calplot

from utils import *

def create_rolling_28D_average(values):
    base_average = np.nanmean(values)
    trailing_twenty_eight = []
    average = []
    for el in values:
        if np.isnan(el):
            el = base_average
        trailing_twenty_eight.append(el)
        base_average = np.mean(trailing_twenty_eight)
        if len(trailing_twenty_eight) < 28:
            numbers = trailing_twenty_eight
        else:
            numbers = trailing_twenty_eight[-28:]
        average.append(np.mean(numbers))
    return average

def plot_minutes_to_target(plot_this, target, experiment_start, ax, limit):
    plot_this = (plot_this - target) * 60
    ax.plot(plot_this.index
      , plot_this
      , color='black'
      , linewidth=.5)
    ax.fill_between(
        plot_this.index
      , [0.0] * plot_this.shape[0]
      , np.minimum([0.0] * plot_this.shape[0], plot_this)
      , color='red'
      , alpha=0.2)
    ax.fill_between(
        plot_this.index
      , [0.0] * plot_this.shape[0]
      , np.maximum([0.0] * plot_this.shape[0], plot_this)
      , color='green'
      , alpha=0.2)
    ax.vlines(
        experiment_start
      , ymin=0
      , ymax=9 * 60
      , color='lightgreen'
      , linestyle='dashed')

    ax.set_ylim(-1 * limit, limit)
    ax.yaxis.set_label_position("right")
    ax.set_facecolor('whitesmoke')
    ax.yaxis.tick_right()
    myFmt = mdates.DateFormatter('%b')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(
        axis='both',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        right=False,
        labelbottom=True,
        labelsize=7)
    ax.set_title(
        'Minutes to Target (Trailing 28 Days)'
      , loc='left'
      , size=7)
    return ax

def launch_dashboard(config):
    st.title("Project Kiwi")
    st.text("We have set up an 'AB' test to determine if Kiwi's do in fact increase the duration and quality of sleep")

    # set up the date basis for all of the plots
    date_idx = pd.date_range(start='2024-01-01', end='2026-12-31', freq='D')
    base_df = pd.DataFrame({
        'date': date_idx.date
      , 'idx': range(len(date_idx))}).set_index('date')
    plot_df = base_df[base_df.index >= dt.date(2025,1,1)]

    st.subheader("Kiwi Treatment Days")
    # Check if experiments date table exist
    if not table_exists(DB, 'experiment'):

        # Generate random days if they don't exist (run experiment over the next three months)
        days = pd.date_range(dt.date.today(), periods = 91, freq = 'D')
        df = pd.DataFrame({'values': np.random.choice([1, 2], size=len(days)), 'date': days})
        df = df.set_index('date')

        # Save experiments date table to database
        df.to_sql('experiment', CONNECTION_STRING, index=True)

    # retrieve the experiments dates
    kiwi_df = retrieve_query("SELECT * FROM experiment;").set_index('date')
    kiwi_df = plot_df.join(kiwi_df)[['values']]

    if table_exists(DB, 'treatment'):
        treatment = retrieve_query("SELECT * FROM treatment;").set_index('date')
        kiwi_df = kiwi_df.join(treatment)
        kiwi_df.loc[~kiwi_df['treatment'].isnull(),'values'] = 4

    # All future experiment days should be a different color
    kiwi_df.loc[(kiwi_df.index.date >= dt.date.today()) & (kiwi_df['values'] > 1), 'values'] = 3
    kiwi_df['values'] = kiwi_df['values'].astype('float64')
    values = kiwi_df['values']

    # Apply random days to calendar
    # --- Grey if prior to or after the experiment
    # --- Light Green if Kiwi taken (past)
    # --- Dark Green if Kiwi Supposed to be taken (future)
    # --- White if Kiwi Not Taken
    # --- Red for days missed
    colors = [
        'whitesmoke'
      , 'darkgreen'
      , 'lightgreen'
      , 'red']
    labels = [
        'No Kiwi'
      , 'Kiwi Eaten'
      , 'Planned Kiwi'
      , 'Forgot Kiwi']
    custom_cmap = ListedColormap(colors, N=len(colors))
    fig, ax = calplot.calplot(
        values
      , fillcolor='lightgrey'
      , linecolor='lightgrey'
      , dropzero=False
      , edgecolor='black'
      , cmap=custom_cmap
      , vmin=1
      , vmax=4
      , colorbar=False)

    legend = plt.legend()
    legend.set_visible(False)

    for i in range(len(colors)):
        plt.plot([], [], c=custom_cmap.colors[i], label=labels[i])

    plt.legend(bbox_to_anchor=(0,2.75), loc='upper left', ncols=4)
    st.pyplot(fig=fig)

    # input kiwi data
    # choose model
    # visualize errors
    # visualize features

    with st.form(key='my_form'):

        left_col, right_col = st.columns(
            [0.7, 0.3]
          , vertical_alignment='bottom')

        with left_col:
            forgot_date = st.selectbox(
                "Did you forget to eat a kiwi for any of these days?"
                , (kiwi_df.index[kiwi_df['values'] == 2]).date
                , index=None
                , placeholder="Forgotten Date")

        with right_col:
            submitted = st.form_submit_button(label="Submit Information")

        if submitted:
            st.write(f"{forgot_date} is being removed from the database.")
            kiwi_df.loc[kiwi_df.index.date==forgot_date, 'values'] = 4
            treatment = kiwi_df[kiwi_df['values'] == 4]
            treatment['treatment'] = True
            treatment[['treatment']].to_sql('treatment', CONNECTION_STRING, index=True, if_exists='replace')
            time.sleep(3)
            st.rerun()



    # Generate Data For Sleep Duration Visualizations
    query = """
    select
        date::date date
      , deep_sleep_duration / 60.0 / 60.0 deep_sleep_duration
      , light_sleep_duration / 60.0 / 60.0  light_sleep_duration
      , rem_sleep_duration / 60.0 / 60.0 rem_sleep_duration
      , total_sleep_duration / 60.0 / 60.0  total_sleep_duration
      , row_number() over (partition by date order by total_sleep_duration desc) rn
    from sleep
    where type = 'long_sleep'
    """

    total_sleep_df = retrieve_query(query)
    total_sleep_df['date'] = pd.to_datetime(total_sleep_df['date'])
    total_sleep_df = total_sleep_df.set_index('date')
    total_sleep_df = total_sleep_df.astype({el: float for el in total_sleep_df.columns})
    total_sleep_df = total_sleep_df[total_sleep_df['rn'] == 1]
    total_sleep_df = base_df.join(total_sleep_df)
    kiwi_df_tmp = kiwi_df.copy().reset_index()
    kiwi_df_tmp.index = kiwi_df_tmp['date'].apply(lambda el: el + relativedelta(days=1))
    kiwi_df_tmp = kiwi_df_tmp.drop('date', axis=1)
    total_sleep_df = total_sleep_df.join(kiwi_df_tmp)
    total_sleep_df = total_sleep_df.drop('idx', axis=1)

    total_sleep_df['total_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['total_sleep_duration'].values)
    total_sleep_df['deep_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['deep_sleep_duration'].values)
    total_sleep_df['rem_sleep_duration_28d'] = create_rolling_28D_average(total_sleep_df['rem_sleep_duration'].values)

    total_sleep_df = plot_df.join(total_sleep_df)
    total_sleep_df = total_sleep_df[total_sleep_df.index.date <= dt.date.today()]

    st.subheader("Last Night's Sleep Statistics")
    yesterday = dt.date.today() + relativedelta(days= -1)
    todays_sleep = total_sleep_df[total_sleep_df.index.date == dt.date.today()]
    total_sleep = todays_sleep['total_sleep_duration'].iloc[0]
    deep_sleep = todays_sleep['deep_sleep_duration'].iloc[0]
    rem_sleep = todays_sleep['rem_sleep_duration'].iloc[0]

    def time_convert(time_float):
        hours = int(np.floor(time_float))
        minutes = int(np.floor((time_float - hours) * 60))
        return hours, minutes

    st.text(f"""
    Last Night's Summary Statistics ({dt.date.today()}):
      - Total Sleep Duration: {time_convert(total_sleep)[0]} hrs and {time_convert(total_sleep)[1]} minutes
      - REM Sleep Duration: {time_convert(rem_sleep)[0]} hrs and {time_convert(rem_sleep)[1]} minutes
      - Deep Sleep Duration: {time_convert(deep_sleep)[0]} hrs and {time_convert(deep_sleep)[1]} minutes
    """)

    st.subheader("Sleep Duration and Quality Visualizations")

    sleep_dimension = st.selectbox(
        "Choose Sleep Dimension"
      , options = [
            'Total Sleep'
          , 'Deep Sleep'
          , 'REM Sleep'
        ])

    params = {
        'Total Sleep': {
            'label': 'total_sleep'
          , 'good': 8
          , 'bad': 6
        }
      , 'Deep Sleep': {
            'label': 'deep_sleep'
          , 'good': 1.5
          , 'bad': 1
        }
      , 'REM Sleep': {
            'label': 'rem_sleep'
          , 'good': 2
          , 'bad': 1.5
        }
    }

    label = params[sleep_dimension]['label']
    good = params[sleep_dimension]['good']
    bad = params[sleep_dimension]['bad']

    # Generate total sleep data summary and plots
    st.markdown(f"##### {sleep_dimension}")

    mean_sleep = total_sleep_df[f'{label}_duration'][-91:].mean()
    current_hours = np.floor(mean_sleep)
    current_minutes = np.floor((mean_sleep - current_hours) * 60)

    target_hours = np.floor(good)
    target_minutes = np.floor((good - target_hours) * 60)

    st.write(f"The average hours of {sleep_dimension} in the last 91 days is {current_hours:.0f} hours and {current_minutes:.0f} minutes. "
             f"The {sleep_dimension} goal is {target_hours:.0f} hours and {target_minutes:.0f} minutes")

    fig, ax = calplot.calplot(
        data=total_sleep_df[f'{label}_duration']
      , fillcolor='whitesmoke'
      , linecolor='lightgrey'
      , dropzero=True
      , edgecolor='black'
      , cmap='RdYlGn'
      , vmin=bad
      , vmax=good)
    st.pyplot(fig=fig)

    fig, ax = plt.subplots(1, figsize=(8, 1.25))
    ax = plot_minutes_to_target(
        total_sleep_df[f'{label}_duration_28d']
      , good
      , kiwi_df[~kiwi_df['values'].isna()].index.min()
      , ax
      , 120)
    st.pyplot(fig=fig, width='content')

    st.subheader("T-Test Visualizations")

    fig, ax = plt.subplots(1, figsize=(8, 4))
    tmp = total_sleep_df[~total_sleep_df[f'{label}_duration'].isna()]
    control = tmp[f'{label}_duration'][tmp['values'] != 2].values
    experiment = tmp[f'{label}_duration'][tmp['values'] == 2].values

    # Perform independent samples t-test
    t_statistic, p_value = stats.ttest_ind(control, experiment)
    st.write(f"T-statistic: {t_statistic:.2f}")
    st.write(f"P-value: {p_value:.4f}")

    bins = ax.hist(control
      , bins=20
      , color='grey'
      , edgecolor='grey'
      , density=True
      , alpha=.4)

    ax.hist(experiment
      , bins=bins[1]
      , color='lightgreen'
      , edgecolor='green'
      , density=True
      , alpha=.4)

    ax.yaxis.set_label_position("right")
    ax.set_facecolor('whitesmoke')
    ax.yaxis.tick_right()
    ax.tick_params(
        axis='both',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        right=False,
        labelbottom=True,
        labelsize=7)
    ax.set_title(
        f'Distribution of {sleep_dimension} Duration [hours]'
      , loc='left'
      , size=7)
    st.pyplot(fig=fig, width='content')

    st.subheader("Modelling Visualizations")