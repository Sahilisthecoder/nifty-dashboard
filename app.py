import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objs as go

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server

# Define layout
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
    html.H2(children="Investment Allocation Suggestion", style={'color': '#1f77b4', 'margin-top': '30px'}),
    html.Div(children='''Based on the calculated probabilities and expected returns...''', style={'font-style': 'italic'})
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
    try:
        # Get data
        nifty_ticker = "^NSEI"
        start_date = "2000-01-01"
        end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
        
        # Download data with progress=False to suppress output
        nifty_data = yf.download(nifty_ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        # Ensure we have data
        if nifty_data.empty:
            raise ValueError("No data returned from Yahoo Finance")
            
        # Calculate yearly returns
        yearly_closing_price = nifty_data['Close'].resample('Y').last()
        annual_returns = yearly_closing_price.pct_change().dropna()
        
        # Convert to 1-dimensional array if needed
        if isinstance(annual_returns, pd.DataFrame):
            annual_returns = annual_returns.squeeze()  # Convert to Series if it's a DataFrame
            
        # Get current year data
        current_year = datetime.datetime.now().year
        start_date_current_year = f"{current_year}-01-01"
        current_year_nifty_data = yf.download(nifty_ticker, start=start_date_current_year, progress=False, auto_adjust=True)
        
        # Monthly returns calculation
        monthly_returns_df = pd.DataFrame()
        if not current_year_nifty_data.empty:
            monthly_closing = current_year_nifty_data['Close'].resample('ME').last()
            monthly_returns = monthly_closing.pct_change().dropna()
            monthly_returns_df = pd.DataFrame({
                'Month': monthly_returns.index.strftime('%Y-%m'),
                'Return': monthly_returns.values
            })
        
        # Probability calculations
        average_return = annual_returns.mean()
        last_return = annual_returns.iloc[-1]
        
        # Filter years with below-average returns
        below_avg_years = annual_returns[annual_returns < average_return]
        total_below_avg = len(below_avg_years)
        
        # Initialize counters
        exceed_next_year = 0
        exceed_next_two_years = 0
        next_year_returns = []
        next_two_year_returns = []
        
        # Analyze historical patterns
        for i in range(len(annual_returns)-2):
            if annual_returns.iloc[i] < average_return:
                # Check next year
                if annual_returns.iloc[i+1] > average_return:
                    exceed_next_year += 1
                next_year_returns.append(annual_returns.iloc[i+1])
                
                # Check next two years average
                two_year_avg = annual_returns.iloc[i+1:i+3].mean()
                if two_year_avg > average_return:
                    exceed_next_two_years += 1
                next_two_year_returns.append(two_year_avg)
        
        # Calculate probabilities
        prob_next_year = exceed_next_year / total_below_avg if total_below_avg > 0 else 0
        prob_next_two_years = exceed_next_two_years / total_below_avg if total_below_avg > 0 else 0
        
        # Calculate expected returns
        exp_next_year = pd.Series(next_year_returns).mean() if next_year_returns else 0
        exp_next_two_years = pd.Series(next_two_year_returns).mean() if next_two_year_returns else 0
        
        # Create figures
        historical_fig = go.Figure(
            data=go.Scatter(
                x=annual_returns.index,
                y=annual_returns,
                mode='lines+markers'
            )
        )
        historical_fig.update_layout(
            title='Historical Annual Returns',
            xaxis_title='Year',
            yaxis_title='Return'
        )
        
        monthly_fig = go.Figure()
        if not monthly_returns_df.empty:
            monthly_fig.add_trace(go.Bar(
                x=monthly_returns_df['Month'],
                y=monthly_returns_df['Return']
            ))
        monthly_fig.update_layout(
            title="Current Year's Monthly Returns",
            xaxis_title='Month',
            yaxis_title='Return'
        )
        
        # Format outputs
        update_status = "Data updated successfully!"
        prob_next_year_text = f"Probability of next year exceeding average: {prob_next_year:.1%}"
        prob_next_two_text = f"Probability of next two years exceeding average: {prob_next_two_years:.1%}"
        exp_next_year_text = f"Expected return next year: {exp_next_year:.1%}"
        exp_next_two_text = f"Expected return next two years: {exp_next_two_years:.1%}"
        
        return (
            update_status,
            historical_fig,
            monthly_fig,
            prob_next_year_text,
            prob_next_two_text,
            exp_next_year_text,
            exp_next_two_text
        )
        
    except Exception as e:
        error_msg = f"Error updating data: {str(e)}"
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error loading data")
        return (error_msg, empty_fig, empty_fig, "", "", "", "")

if __name__ == '__main__':
    app.run_server(debug=True)
