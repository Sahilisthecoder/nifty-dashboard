import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objs as go
import os

app = dash.Dash(__name__)
server = app.server

nifty_ticker = "^NSEI"
start_date = "2000-01-01"
end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
nifty_data = yf.download(nifty_ticker, start=start_date, end=end_date)

yearly_closing_price = nifty_data['Close'].resample('Y').last()
annual_returns = yearly_closing_price.pct_change().dropna()

current_year = datetime.datetime.now().year
start_date_current_year = f"{current_year}-01-01"
current_year_nifty_data = yf.download(nifty_ticker, start=start_date_current_year)

monthly_returns_df = pd.DataFrame()
if not current_year_nifty_data.empty:
    monthly_closing_prices = current_year_nifty_data['Close'].resample('ME').last()
    monthly_returns = monthly_closing_prices.pct_change().dropna()
    monthly_returns_df = monthly_returns.to_frame(name='Return')
    monthly_returns_df['Month'] = monthly_returns_df.index.strftime('%Y-%m')

average_annual_return = annual_returns.mean()
average_return_scalar = average_annual_return if not isinstance(average_annual_return, pd.Series) else average_annual_return.iloc[0]
last_annual_return_scalar = annual_returns.iloc[-1] if not isinstance(annual_returns.iloc[-1], pd.Series) else annual_returns.iloc[-1].iloc[0]

similar_periods_filtered = annual_returns[annual_returns < average_return_scalar]
exceed_average_next_year_count = 0
exceed_average_next_two_years_count = 0
total_similar_periods = len(similar_periods_filtered)

for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 1 < len(annual_returns):
        next_year_return_val = annual_returns.iloc[actual_year_index + 1] if not isinstance(annual_returns.iloc[actual_year_index + 1], pd.Series) else annual_returns.iloc[actual_year_index + 1].iloc[0]
        if next_year_return_val > average_return_scalar:
            exceed_average_next_year_count += 1
    if actual_year_index + 2 < len(annual_returns):
        next_two_years_returns_avg_val = annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean()
        next_two_years_returns_avg_val = next_two_years_returns_avg_val if not isinstance(next_two_years_returns_avg_val, pd.Series) else next_two_years_returns_avg_val.iloc[0]
        if next_two_years_returns_avg_val > average_return_scalar:
            exceed_average_next_two_years_count += 1

probability_next_year = (exceed_average_next_year_count / total_similar_periods) if total_similar_periods > 0 else 0
probability_next_two_years = (exceed_average_next_two_years_count / total_similar_periods) if total_similar_periods > 0 else 0

next_year_returns_after_similar = []
for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 1 < len(annual_returns):
        next_year_returns_after_similar.append(annual_returns.iloc[actual_year_index + 1] if not isinstance(annual_returns.iloc[actual_year_index + 1], pd.Series) else annual_returns.iloc[actual_year_index + 1].iloc[0])

expected_return_next_year_mean_reversion = pd.Series(next_year_returns_after_similar).mean() if next_year_returns_after_similar else 0.0

next_two_years_returns_after_similar = []
for period_end_year in similar_periods_filtered.index[:-2]:
    actual_year_index = annual_returns.index.get_loc(period_end_year)
    if actual_year_index + 2 < len(annual_returns):
        avg = annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean()
        avg = avg if not isinstance(avg, pd.Series) else avg.iloc[0]
        next_two_years_returns_after_similar.append(avg)

expected_return_next_two_years_mean_reversion = pd.Series(next_two_years_returns_after_similar).mean() if next_two_years_returns_after_similar else 0.0

app.layout = html.Div(style={'font-family': 'sans-serif', 'margin': '20px'}, children=[
    html.H1(children='Nifty Market Analysis Dashboard', style={'color': '#1f77b4'}),

    html.Div(children='Analyzing Historical and Current Nifty Performance.', style={'margin-bottom': '20px'}),

    html.Button('Update Data', id='update-button', n_clicks=0, style={'margin-bottom': '20px'}),

    html.Div(id='update-status', style={'margin-bottom': '20px', 'font-weight': 'bold'}),

    html.H2(children='Historical Yearly Returns', style={'color': '#1f77b4'}),
    dcc.Graph(id='historical-returns-graph'),

    html.H2(children="Current Year's Monthly Returns", style={'color': '#1f77b4'}),
    dcc.Graph(id='monthly-returns-graph'),

    html.H2(children="Probability of Exceeding Average Return", style={'color': '#1f77b4'}),
    html.Div(id='prob-next-year-display'),
    html.Div(id='prob-next-two-years-display'),

    html.H2(children="Expected Return due to Mean Reversion", style={'color': '#1f77b4'}),
    html.Div(id='expected-return-next-year-display'),
    html.Div(id='expected-return-next-two-years-display'),
])

@app.callback(
    [Output('update-status', 'children'),
     Output('historical-returns-graph', 'figure'),
     Output('monthly-returns-graph', 'figure'),
     Output('prob-next-year-display', 'children'),
     Output('prob-next-two-years-display', 'children'),
     Output('expected-return-next-year-display', 'children'),
     Output('expected-return-next-two-years-display', 'children')],
    Input('update-button', 'n_clicks')
)
def update_data(n_clicks):
    nifty_ticker = "^NSEI"
    start_date = "2000-01-01"
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    nifty_data = yf.download(nifty_ticker, start=start_date, end=end_date)

    yearly_closing_price = nifty_data['Close'].resample('Y').last()
    annual_returns = yearly_closing_price.pct_change().dropna()

    current_year = datetime.datetime.now().year
    start_date_current_year = f"{current_year}-01-01"
    current_year_nifty_data = yf.download(nifty_ticker, start=start_date_current_year)

    monthly_returns_df = pd.DataFrame()
    if not current_year_nifty_data.empty:
        monthly_closing_prices = current_year_nifty_data['Close'].resample('ME').last()
        monthly_returns = monthly_closing_prices.pct_change().dropna()
        monthly_returns_df = monthly_returns.to_frame(name='Return')
        monthly_returns_df['Month'] = monthly_returns_df.index.strftime('%Y-%m')

    average_annual_return = annual_returns.mean()
    average_return_scalar = average_annual_return if not isinstance(average_annual_return, pd.Series) else average_annual_return.iloc[0]
    last_annual_return_scalar = annual_returns.iloc[-1] if not isinstance(annual_returns.iloc[-1], pd.Series) else annual_returns.iloc[-1].iloc[0]

    similar_periods_filtered = annual_returns[annual_returns < average_return_scalar]
    exceed_average_next_year_count = 0
    exceed_average_next_two_years_count = 0
    total_similar_periods = len(similar_periods_filtered)

    for period_end_year in similar_periods_filtered.index[:-2]:
        actual_year_index = annual_returns.index.get_loc(period_end_year)
        if actual_year_index + 1 < len(annual_returns):
            next_year_return_val = annual_returns.iloc[actual_year_index + 1] if not isinstance(annual_returns.iloc[actual_year_index + 1], pd.Series) else annual_returns.iloc[actual_year_index + 1].iloc[0]
            if next_year_return_val > average_return_scalar:
                exceed_average_next_year_count += 1
        if actual_year_index + 2 < len(annual_returns):
            next_two_years_returns_avg_val = annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean()
            next_two_years_returns_avg_val = next_two_years_returns_avg_val if not isinstance(next_two_years_returns_avg_val, pd.Series) else next_two_years_returns_avg_val.iloc[0]
            if next_two_years_returns_avg_val > average_return_scalar:
                exceed_average_next_two_years_count += 1

    probability_next_year = (exceed_average_next_year_count / total_similar_periods) if total_similar_periods > 0 else 0
    probability_next_two_years = (exceed_average_next_two_years_count / total_similar_periods) if total_similar_periods > 0 else 0

    next_year_returns_after_similar = []
    for period_end_year in similar_periods_filtered.index[:-2]:
        actual_year_index = annual_returns.index.get_loc(period_end_year)
        if actual_year_index + 1 < len(annual_returns):
            next_year_returns_after_similar.append(annual_returns.iloc[actual_year_index + 1] if not isinstance(annual_returns.iloc[actual_year_index + 1], pd.Series) else annual_returns.iloc[actual_year_index + 1].iloc[0])

    expected_return_next_year_mean_reversion = pd.Series(next_year_returns_after_similar).mean() if next_year_returns_after_similar else 0.0

    next_two_years_returns_after_similar = []
    for period_end_year in similar_periods_filtered.index[:-2]:
        actual_year_index = annual_returns.index.get_loc(period_end_year)
        if actual_year_index + 2 < len(annual_returns):
            avg = annual_returns.iloc[actual_year_index + 1 : actual_year_index + 3].mean()
            avg = avg if not isinstance(avg, pd.Series) else avg.iloc[0]
            next_two_years_returns_after_similar.append(avg)

    expected_return_next_two_years_mean_reversion = pd.Series(next_two_years_returns_after_similar).mean() if next_two_years_returns_after_similar else 0.0

    historical_returns_figure = go.Figure(data=go.Scatter(x=annual_returns.index, y=annual_returns.values, mode='lines+markers'))
    historical_returns_figure.update_layout(title='Historical Annual Returns', xaxis_title='Year', yaxis_title='Return')

    monthly_returns_figure = go.Figure(data=go.Bar(x=monthly_returns_df['Month'], y=monthly_returns_df['Return']))
    monthly_returns_figure.update_layout(title="Current Year's Monthly Returns", xaxis_title='Month', yaxis_title='Return')

    return (
        "Data updated successfully!",
        historical_returns_figure,
        monthly_returns_figure,
        f"Probability of next year exceeding average: {probability_next_year:.4f}",
        f"Probability of next two years exceeding average: {probability_next_two_years:.4f}",
        f"Expected return next year: {expected_return_next_year_mean_reversion:.4f}",
        f"Expected return next two years: {expected_return_next_two_years_mean_reversion:.4f}"
    )

if __name__ == '__main__':
    app.run_server(debug=True)
