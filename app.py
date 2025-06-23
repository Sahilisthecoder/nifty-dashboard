import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objs as go

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # This is needed for render.com deployment

# Define layout first to ensure app can start without immediate data loading
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
    html.H2(children="Investment Allocation Suggestion (Conceptual)", style={'color': '#1f77b4', 'margin-top': '30px'}),
    html.Div(children='''Based on the calculated probabilities and expected returns...''', style={'font-style': 'italic'})
])

# Define the callback to update data on button click
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
    try:
        # Re-run data acquisition and calculations
        nifty_ticker = "^NSEI"
        start_date = "2000-01-01"
        end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
        nifty_data = yf.download(nifty_ticker, start=start_date, end=end_date, auto_adjust=True)

        yearly_closing_price = nifty_data['Close'].resample('Y').last()
        annual_returns = yearly_closing_price.pct_change().dropna()

        current_year = datetime.datetime.now().year
        start_date_current_year = f"{current_year}-01-01"
        current_year_nifty_data = yf.download(nifty_ticker, start=start_date_current_year, auto_adjust=True)

        # Monthly Tracking
        monthly_returns_df = pd.DataFrame()  # Initialize empty DataFrame
        if not current_year_nifty_data.empty:
            monthly_closing_prices = current_year_nifty_data['Close'].resample('ME').last()
            monthly_returns = monthly_closing_prices.pct_change().dropna()
            # Convert to DataFrame properly
            monthly_returns_df = pd.DataFrame({
                'Return': monthly_returns.values,
                'Month': monthly_returns.index.strftime('%Y-%m')
            })

        # Probability Calculation
        average_annual_return = annual_returns.mean()
        average_return_scalar = average_annual_return.iloc[0] if isinstance(average_annual_return, pd.Series) else average_annual_return
        last_annual_return_scalar = annual_returns.iloc[-1]

        similar_periods_filtered = annual_returns[annual_returns < average_return_scalar]

        exceed_average_next_year_count = 0
        exceed_average_next_two_years_count = 0
        total_similar_periods = len(similar_periods_filtered)

        for i in range(len(similar_periods_filtered)-2):
            if i + 1 < len(annual_returns):
                next_year_return_val = annual_returns.iloc[i + 1]
                if next_year_return_val > average_return_scalar:
                    exceed_average_next_year_count += 1
            if i + 2 < len(annual_returns):
                next_two_years_returns_avg_val = annual_returns.iloc[i + 1:i + 3].mean()
                if next_two_years_returns_avg_val > average_return_scalar:
                    exceed_average_next_two_years_count += 1

        probability_next_year = (exceed_average_next_year_count / total_similar_periods) if total_similar_periods > 0 else 0
        probability_next_two_years = (exceed_average_next_two_years_count / total_similar_periods) if total_similar_periods > 0 else 0

        # Mean Reversion Analysis
        next_year_returns_after_similar = []
        next_two_years_returns_after_similar = []
        
        for i in range(len(similar_periods_filtered)-2):
            if i + 1 < len(annual_returns):
                next_year_returns_after_similar.append(annual_returns.iloc[i + 1])
            if i + 2 < len(annual_returns):
                next_two_years_returns_after_similar.append(annual_returns.iloc[i + 1:i + 3].mean())

        expected_return_next_year_mean_reversion = pd.Series(next_year_returns_after_similar).mean() if next_year_returns_after_similar else 0.0
        expected_return_next_two_years_mean_reversion = pd.Series(next_two_years_returns_after_similar).mean() if next_two_years_returns_after_similar else 0.0

        # Generate figures
        historical_returns_figure = go.Figure(data=go.Scatter(
            x=annual_returns.index, 
            y=annual_returns,
            mode='lines+markers'
        ))
        historical_returns_figure.update_layout(
            title='Historical Annual Returns',
            xaxis_title='Year',
            yaxis_title='Return'
        )

        monthly_returns_figure = go.Figure()
        if not monthly_returns_df.empty:
            monthly_returns_figure.add_trace(go.Bar(
                x=monthly_returns_df['Month'],
                y=monthly_returns_df['Return']
            ))
        monthly_returns_figure.update_layout(
            title="Current Year's Monthly Returns",
            xaxis_title='Month',
            yaxis_title='Return'
        )

        # Update the dashboard elements
        update_status_text = "Data updated successfully!"
        prob_next_year_display = f"Probability of next year exceeding average: {probability_next_year:.2%}"
        prob_next_two_years_display = f"Probability of next two years exceeding average: {probability_next_two_years:.2%}"
        expected_return_next_year_display = f"Expected return next year: {expected_return_next_year_mean_reversion:.2%}"
        expected_return_next_two_years_display = f"Expected return next two years: {expected_return_next_two_years_mean_reversion:.2%}"

        return (update_status_text,
                historical_returns_figure,
                monthly_returns_figure,
                prob_next_year_display,
                prob_next_two_years_display,
                expected_return_next_year_display,
                expected_return_next_two_years_display)

    except Exception as e:
        error_message = f"Error updating data: {str(e)}"
        empty_figure = go.Figure()
        empty_figure.update_layout(title="Error loading data")
        return (error_message, empty_figure, empty_figure, "", "", "", "")

if __name__ == '__main__':
    app.run_server(debug=True)
