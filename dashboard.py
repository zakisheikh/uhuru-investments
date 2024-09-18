import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.title("Stock Dashboard")

# Add your company logo
st.image("UHURULOGO.jpg", width=200)  # Adjust the width as needed

# Input for stock ticker
ticker = st.text_input("Enter Stock Ticker:", "AAPL")

# Select time frame
time_frame = st.selectbox("Select Time Frame:", ["1m", "5m", "1d", "5d", "1w", "1mo"])

# Default data loading based on selected time frame
if time_frame == "1d":
    # Load last 6 months of data for daily interval
    default_start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
elif time_frame == "1w":
    # Load last year of data for weekly interval
    default_start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
else:
    # For other intervals, default start date could be set to None or to the earliest date
    default_start_date = None

if st.button("Get Stock Data"):
    try:
        # If default_start_date is set, use it to fetch data
        if default_start_date:
            response = requests.get(f'http://127.0.0.1:5000/stock/{ticker}/{time_frame}?start_date={default_start_date}')
        else:
            response = requests.get(f'http://127.0.0.1:5000/stock/{ticker}/{time_frame}')

        # Check if the response is successful
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)

            # Format price data to two decimal places
            df['Close'] = df['Close'].round(2)
            df['Open'] = df['Open'].round(2)
            df['High'] = df['High'].round(2)
            df['Low'] = df['Low'].round(2)

            # Format the 'Date' column to MM/DD/YY with UTC handling
            df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.strftime('%m/%d/%y')

            # Set the 'Date' as the index for plotting
            df.set_index('Date', inplace=True)

            # Create the Plotly figure
            fig = go.Figure()

            # Candlestick chart for price action
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Candlestick',
                increasing_line_color='green',
                decreasing_line_color='red',
                hovertemplate=(
                    "Date: %{x}<br>" +
                    "Open: %{y0}<br>" +
                    "High: %{y2}<br>" +
                    "Low: %{y1}<br>" +
                    "Close: %{y3}<br>" +
                    "Volume: %{customdata}<br>" +
                    "<extra></extra>"
                ),
                customdata=df['Volume']  # Include volume for hover
            ))

            # Determine color for volume bars
            volume_color = ['green' if close >= open else 'red' for close, open in zip(df['Close'], df['Open'])]

            # Create a separate figure for volume
            volume_fig = go.Figure()

            # Volume bar chart with color based on price movement
            volume_fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=volume_color
            ))

            # Add moving averages for the price
            if 'MA21' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['MA21'], mode='lines', name='MA21', line=dict(color='orange', dash='dash')))
            if 'MA50' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50', line=dict(color='blue', dash='dash')))
            if 'MA200' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='MA200', line=dict(color='red', dash='dash')))

            # Get the last price for display
            last_price = df['Close'].iloc[-1]

            # Update layout for the main price chart
            fig.update_layout(
                title=f"{ticker} Stock Price - Last Price: ${last_price:.2f}",
                xaxis_title="Date",
                yaxis_title="Price",
                template='plotly_white',
                height=600,
                xaxis_rangeslider_visible=False
            )

            # Show the candlestick plot in Streamlit
            st.plotly_chart(fig)

            # Update layout for the volume chart without title
            volume_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Volume",
                template='plotly_white',
                height=300,
                showlegend=False  # Hide legend for volume
            )

            # Show the volume plot in Streamlit right below the candlestick
            st.plotly_chart(volume_fig)

            # Key information display
            st.markdown("""
            **Key:**
            - **Green Volume Bars**: Closing price was higher than the opening price.
            - **Red Volume Bars**: Closing price was lower than the opening price.
            """)

        elif response.status_code == 404:
            st.error("Error fetching data: " + response.json()['error'])
        else:
            st.error("An unexpected error occurred.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
