import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="공영주차장 정보",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 공영주차장 정보 제공 서비스")

# -----------------------------
# CSV 업로드
# -----------------------------
uploaded_file = st.file_uploader(
    "공영주차장 CSV 업로드",
    type=["csv"]
)

# -----------------------------
# CSV 읽기 함수
# -----------------------------
def load_csv(file):
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]

    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc)
        except:
            continue

    st.error("CSV 파일을 읽을 수 없습니다.")
    st.stop()


if uploaded_file is not None:

    df = load_csv(uploaded_file)

    # 숫자형 변환
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
    df["기본 주차 요금"] = pd.to_numeric(df["기본 주차 요금"], errors="coerce")

    # 결측 제거
    df = df.dropna(subset=["위도", "경도"])

    st.success("CSV 업로드 완료!")

    st.subheader("데이터 미리보기")
    st.dataframe(df)

    # -----------------------------
    # 주소 검색
    # -----------------------------
    st.subheader("🔍 주소 검색")

    keyword = st.text_input("주소를 입력하세요")

    if keyword:

        result = df[df["주소"].astype(str).str.contains(keyword, na=False)]

        if len(result) == 0:
            st.warning("검색 결과가 없습니다.")

        else:

            st.success(f"{len(result)}건 검색되었습니다.")

            st.dataframe(
                result[
                    [
                        "주차장명",
                        "주소",
                        "기본 주차 요금"
                    ]
                ]
            )

    # -----------------------------
    # 지도
    # -----------------------------
    st.subheader("🗺️ 공영주차장 지도")

    center_lat = df["위도"].mean()
    center_lon = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11
    )

    for _, row in df.iterrows():

        popup = f"""
        <b>{row['주차장명']}</b><br>
        주소 : {row['주소']}<br>
        기본요금 : {row['기본 주차 요금']}원
        """

        tooltip = f"""
        {row['주소']}<br>
        기본요금 : {row['기본 주차 요금']}원
        """

        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=1200,
        height=600
    )
