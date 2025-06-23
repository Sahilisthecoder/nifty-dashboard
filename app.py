import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objs as go

# Initialize the Dash app
# The __name__ is important for deployment
app = dash.Dash(__name__)
server = app.server # This is needed for render.com deployment

# Initial data loading and calculations
# This will run when the app starts
nifty_ticker = "^NSEI"
start_date = "2000-01-01"
end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
nifty_data = yf.download(nifty_ticker, start=start_date, end=end_date)

yearly_closing_price = nifty_data['Close'].resample('Y').last()
annual_returns = yearly_closing_price.pct_change().dropna()

current_year = datetime.datetime.now().year
start_date_current_year = f"{current_year}-01-01"
current_year_nifty_data = yf.download(nifty_ticker, start=start_date_current_year)

# Calculate the current year's return (not used directly in display but kept for completeness)
current_year_return = None
if not current_year_nifty_data.empty:
    first_close = current_year_nifty_data['Close'].iloc[0]
    last_close = current_year_nifty_data['Close'].iloc[-1]
    current_year_return = (last_close - first_close) / first_close


# Monthly Tracking
monthly_returns_current_year = {}
monthly_returns_df = pd.DataFrame() # Use a DataFrame for plotting
if not current_year_nifty_data.empty:
    monthly_closing_prices = current_year_nifty_data['Close'].resample('ME').last()
    monthly_returns = monthly_closing_prices.pct_change().dropna()

    # Check if monthly_returns is a Series before converting to DataFrame
    if isinstance(monthly_returns, pd.Series):
        monthly_returns_df = monthly_returns.to_frame(name='Return')
    elif isinstance(monthly_returns, pd.DataFrame):
        monthly_returns_df = monthly_returns # It's already a DataFrame
        monthly_returns_df.columns = ['Return'] # Ensure column name is 'Return'

    if not monthly_returns_df.empty:
        monthly_returns_df['Month'] = monthly_returns_df.index.strftime('%Y-%m')
        for index, value in monthly_returns_df.iterrows():
             month = index.strftime('%Y-%m')
             monthly_returns_current_year[month] = value['Return'] # Access value correctly from DataFrame row


# Probability Calculation
average_annual_return = annual_returns.mean()
average_return_scalar = average_annual_return.iloc[0] if isinstance(average_annual_return, pd.Series) else average_annual_return
last_annual_return_scalar = annual_returns.iloc[-1].iloc[0] if isinstance(annual_returns.iloc[-1], pd.Series) else annual_returns.iloc[-1]


recent_trend_condition = last_annual_return_scalar < average_return_scalar
similar_periods_filtered = annual_returns[annual_returns.iloc[:, 0] < average_return_scalar]

exceed_average_next_year_count = 0
exceed_average_next_two_years_count = 0
total_similar_periods = len(similar_periods_filtered)

for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 1 < len(annual_returns):
        next_year_return_val = annual_returns.iloc[actual_year_index + 1].iloc[0]
        if next_year_return_val > average_return_scalar:
            exceed_average_next_year_count += 1
        if actual_year_index + 2 < len(annual_returns):
            next_two_years_returns_avg_val = annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean().iloc[0]
            if next_two_years_returns_avg_val > average_return_scalar:
                exceed_average_next_two_years_count += 1


probability_next_year = (exceed_average_next_year_count / total_similar_periods) if total_similar_periods > 0 else 0
probability_next_two_years = (exceed_average_next_two_years_count / total_similar_periods) if total_similar_periods > 0 else 0

# Mean Reversion Analysis
next_year_returns_after_similar = []
for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 1 < len(annual_returns):
        next_year_returns_after_similar.append(annual_returns.iloc[actual_year_index + 1].iloc[0])

expected_return_next_year_mean_reversion = pd.Series(next_year_returns_after_similar).mean() if next_year_returns_after_similar else 0.0

next_two_years_returns_after_similar = []
for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 2 < len(annual_returns):
        next_two_years_returns_after_similar.append(annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean().iloc[0])

expected_return_next_two_years_mean_reversion = pd.Series(next_two_years_returns_after_similar).mean() if next_two_years_returns_after_similar else 0.0


# Define the layout of the dashboard
app.layout = html.Div(style={'font-family': 'sans-serif', 'margin': '20px'}, children=[
    html.H1(children='Nifty Market Analysis Dashboard', style={'color': '#1f77b4'}),

    html.Div(children='''
        Analyzing Historical and Current Nifty Performance.
