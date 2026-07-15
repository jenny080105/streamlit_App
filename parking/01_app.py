import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="공영주차장 정보",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 공영주차장 정보 제공 서비스")

st.write("CSV 파일을 업로드하세요.")

uploaded_file = st.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success("데이터 업로드 완료!")

    st.subheader("데이터")

    st.dataframe(df)

    st.divider()

    st.subheader("주소 검색")

    keyword = st.text_input("주소를 입력하세요.")

    if keyword:

        result = df[df["주소"].str.contains(keyword, case=False, na=False)]

        if len(result) > 0:

            st.success(f"{len(result)}개의 결과")

            st.dataframe(
                result[["주차장명", "주소", "기본요금"]]
            )

        else:

            st.warning("검색 결과가 없습니다.")

    st.divider()

    st.subheader("공영주차장 지도")

    center_lat = df["위도"].mean()
    center_lon = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12
    )

    for _, row in df.iterrows():

        popup = f"""
        <b>{row['주차장명']}</b><br>
        주소 : {row['주소']}<br>
        요금 : {row['기본요금']}
        """

        tooltip = f"""
        {row['주소']}
        <br>
        {row['기본요금']}
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
