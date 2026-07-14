import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="🌍 Global Top 10 Market Cap Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 글로벌 시가총액 Top 10 주가 비교")
st.write("최근 1년간 주가를 시작 시점을 100으로 정규화하여 비교합니다.")

# 글로벌 시가총액 상위 기업
stocks = {
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Tesla": "TSLA",
    "Saudi Aramco": "2222.SR"
}

period = st.sidebar.selectbox(
    "조회 기간",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

selected = st.sidebar.multiselect(
    "기업 선택",
    list(stocks.keys()),
    default=list(stocks.keys())
)

@st.cache_data
def load_data(period):
    df = pd.DataFrame()

    for company, ticker in stocks.items():

        try:
            data = yf.download(
                ticker,
                period=period,
                auto_adjust=True,
                progress=False
            )

            if not data.empty:
                close = data["Close"]

                # yfinance 버전 호환
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                df[company] = close

        except Exception:
            pass

    return df


prices = load_data(period)

if prices.empty:
    st.error("주가 데이터를 가져오지 못했습니다.")
    st.stop()

prices = prices[selected]

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
    title="최근 주가 변화 (시작=100)",
    template="plotly_dark",
    height=700,
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="정규화 가격"
)

st.plotly_chart(fig, use_container_width=True)

returns = ((prices.iloc[-1] / prices.iloc[0]) - 1) * 100

summary = pd.DataFrame({
    "현재가": prices.iloc[-1].round(2),
    "수익률(%)": returns.round(2)
})

summary = summary.sort_values("수익률(%)", ascending=False)

st.subheader("📊 수익률 순위")

st.dataframe(summary, use_container_width=True)

st.subheader("📈 최고 수익 기업")

best = summary.index[0]

st.success(
    f"{best} : {summary.iloc[0]['수익률(%)']:.2f}%"
)
