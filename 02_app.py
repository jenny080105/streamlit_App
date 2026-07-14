streamlit
yfinance
pandas
plotly
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Global Top10 Market Cap Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 Global Top10 Market Cap Stocks")
st.caption("최근 1년 주가 변화")

# 글로벌 시가총액 Top10 (2025 기준)
stocks = {
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Tesla": "TSLA"
}

end = datetime.today()
start = end - timedelta(days=365)

@st.cache_data
def load_data():

    price_df = pd.DataFrame()

    for name, ticker in stocks.items():

        data = yf.download(
            ticker,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True
        )

        if len(data) > 0:
            price_df[name] = data["Close"]

    return price_df

prices = load_data()

# 시작값을 100으로 정규화
normalized = prices / prices.iloc[0] * 100

fig = go.Figure()

for company in normalized.columns:

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[company],
            mode="lines",
            name=company,
            line=dict(width=2)
        )
    )

fig.update_layout(
    title="최근 1년 수익률 비교 (시작=100)",
    template="plotly_dark",
    height=700,
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Normalized Price"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

latest = pd.DataFrame({
    "현재가": prices.iloc[-1].round(2),
    "1년 수익률(%)":
        ((prices.iloc[-1]/prices.iloc[0]-1)*100).round(2)
})

latest = latest.sort_values("1년 수익률(%)", ascending=False)

st.subheader("📊 Performance")

st.dataframe(
    latest,
    use_container_width=True
)
