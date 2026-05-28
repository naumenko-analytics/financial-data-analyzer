# Financial Data Analyzer
# Naumenko Analytics LLC
# Author: Maksym Naumenko

# Imports
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title = "Financial Data Analyzer | Naumenko Analytics", layout = "wide")

# Header
st.title("Financial Data Analyzer")
st.markdown("**Naumenko Analytics LLC** | Real-time stock analysis and financial metrics")
st.divider()

# Sidebar with user inputs
st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Stock Ticker Symbol", value = "AAPL", 
                               help = "Enter a valid stock ticker (AAPL, TSLA, MSFT, GOOGL, ...)")

period = st.sidebar.selectbox("Select Time Period", options = ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                              index = 3, format_func = lambda x: {
                                  "1mo": "1 Month",
                                  "3mo": "3 Months",
                                  "6mo": "6 Months",
                                  "1y": "1 Year",
                                  "2y": "2 Years",
                                  "5y": "5 Years"
                              }[x])

# Fetching data
@st.cache_data(ttl=300)
def get_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period = period)
        info = stock.info
        return df, info
    except Exception as e:
        return None, None
    
df, info = get_stock_data(ticker, period)

if df is None or info is None:
    st.error(f"Could not fetch data for '{ticker}'. Please check the ticker symbol.")
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Company",
        value=info.get("shortName", ticker)
    )

with col2:
    st.metric(
        label="Sector",
        value=info.get("sector", "N/A")
    )

with col3:
    st.metric(
        label="Market Cap",
        value=f"${info.get('marketCap', 0)/1e9:.2f}B"
    )

st.divider()

# Key Metrics
st.subheader("Key Metrics")

current_price = df['Close'].iloc[-1]
prev_price = df['Close'].iloc[-2]
price_change = current_price - prev_price
price_change_pct = (price_change / prev_price) * 100

high_52w = df['Close'].max()
low_52w = df['Close'].min()
avg_volume = df['Volume'].mean()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Current Price",
        value=f"${current_price:.2f}",
        delta=f"{price_change_pct:.2f}%"
    )

with col2:
    st.metric(
        label="Period High",
        value=f"${high_52w:.2f}"
    )

with col3:
    st.metric(
        label="Period Low",
        value=f"${low_52w:.2f}"
    )

with col4:
    st.metric(
        label="Avg Volume",
        value=f"{avg_volume/1e6:.2f}M"
    )

with col5:
    st.metric(
        label="Price Range",
        value=f"${high_52w - low_52w:.2f}"
    )

st.divider()

# Price Chart
st.subheader("Price Chart")

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

fig.add_trace(
    go.Candlestick(
        x=df.index, open=df['Open'], 
        high=df['High'], low=df['Low'], 
        close= df['Close'], name='Price'
        ), 
        row =1, col=1)

# Moving Averages
ma20 = df['Close'].rolling(window=20).mean()
ma50 = df['Close'].rolling(window=50).mean()

fig.add_trace(
    go.Scatter(
        x = df.index,
        y = ma20,
        name = '20-day MA',
        line = dict(color='orange', width = 1.5)
    ),
    row=1, col=1)

fig.add_trace(
    go.Scatter(
        x = df.index,
        y = ma50,
        name = '50-day MA',
        line = dict(color='blue', width = 1.5)
    )
)

fig.add_trace(
    go.Bar(
        x=df.index,
        y=df['Volume'],
        name="Volume",
        marker_color='lightgreen'
    ),
    row=2, col=1
)

fig.update_layout(
    height = 600,
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    legend=dict(orientation="h", y=1.02)
)

fig.update_yaxes(title_text="Price (USD)", row = 1, col = 1)
fig.update_yaxes(title_text="Volume", row = 2, col=1)

st.plotly_chart(fig, use_container_width=True)
st.divider()

# Returns Analysis
st.subheader("Returns Analysis")

df['Daily Return'] = df['Close'].pct_change()
df['Cumulative Return'] = (1 + df['Daily Return']).cumprod() - 1

col1, col2 = st.columns(2)

with col1:
    fig_returns = go.Figure()
    fig_returns.add_trace(
        go.Histogram(
            x=df['Daily Return'].dropna(),
            nbinsx = 50,
            name='Daily Returns',
            marker_color='steelblue'
        )
    )

    fig_returns.update_layout(
        title='Daily Returns Distribution',
        xaxis_title = "Daily Return",
        yaxis_title = "Frequency",
        template = 'plotly_white',
        height = 400
    )
    st.plotly_chart(fig_returns, use_container_width = True)

with col2:
    fig_cumulative = go.Figure()
    fig_cumulative.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Cumulative Return'] * 100,
            fill = 'tozeroy',
            name = 'Cumulative Return',
            line = dict(color='green', width=2),
        )
    )
    fig_cumulative.update_layout(
        title = "Cumulative Return (%)",
        xaxis_title = "Date",
        yaxis_title = "Retrun (%)",
        template = 'plotly_white',
        height = 400
    )
    st.plotly_chart(fig_cumulative, use_container_width = True)

st.divider()

# Risk Metrics
st.subheader("Risk Metrics")

daily_returns = df['Daily Return'].dropna()

volatility = daily_returns.std() * np.sqrt(252)
sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))
max_drawdown = ((df['Close'] / df['Close'].cummax()) - 1).min()
total_return = df['Cumulative Return'].iloc[-1]
positive_days = (daily_returns > 0).sum()
negative_days = (daily_returns < 0).sum()
win_rate = positive_days / (positive_days + negative_days)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Annual Volatility",
        value=f'{volatility * 100:.2f}%',
        help = "Annualized standard deviation of daily returns"
    )

with col2:
    st.metric(
        label='Sharpe Ratio',
        value=f'{sharpe_ratio:.2f}',
        help = "Risk-adjusted return (higher is better)"
    )

with col3:
    st.metric(
        label='Max Drawdown',
        value=f'{max_drawdown * 100:.2f}%',
        help = "Largest peak-to-through decline"
    )

with col4:
    st.metric(
        label='Win Rate',
        value=f'{win_rate*100:.1f}%',
        help='Percentage of days with positive returns'
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label='Total Return',
        value=f'{total_return*100:.2f}%'
    )

with col2:
    st.metric(
        label='Positive/Negative Days',
        value=f'{positive_days} / {negative_days}'
    )


# Footer
st.divider()
st.caption("Built by Naumenko Analytics LLC | Data provided by Yahoo Finance via yfinance | For educational and analytical purposes only")