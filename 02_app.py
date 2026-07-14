import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title="주식 대시보드", layout="wide")

st.title("🌍 글로벌 시가총액 TOP10")

companies = {
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Saudi Aramco": "2222.SR",
}

@st.cache_data
def load_data():
    result = pd.DataFrame()

    for name, ticker in companies.items():
        df = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True,
        )

        if not df.empty:
            result[name] = df["Close"]

    return result


prices = load_data()

prices = prices / prices.iloc[0] * 100

fig = px.line(
    prices,
    x=prices.index,
    y=prices.columns,
    title="최근 1년 주가 변화 (시작=100)"
)

st.plotly_chart(fig, use_container_width=True)
