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

uploaded_file = st.file_uploader(
    "공영주차장 CSV 업로드",
    type=["csv"]
)

# CSV 읽기 함수 (UTF-8, CP949, EUC-KR 모두 지원)
def load_csv(file):
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]

    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc)
        except Exception:
            continue

    st.error("CSV 파일을 읽을 수 없습니다.")
    st.stop()

if uploaded_file is not None:

    df = load_csv(uploaded_file)

    st.success("CSV 업로드 완료!")

    st.write(df)

    # 컬럼명 확인
    st.subheader("컬럼명")
    st.write(df.columns.tolist())

    # 필요한 컬럼 확인
    required = ["주차장명", "주소", "위도", "경도", "기본요금"]

    if not all(col in df.columns for col in required):
        st.error("CSV에 필요한 컬럼이 없습니다.")
        st.write("필요한 컬럼")
        st.write(required)
        st.stop()

    # 주소 검색
    st.subheader("주소 검색")

    keyword = st.text_input("주소 입력")

    if keyword:

        result = df[df["주소"].astype(str).str.contains(keyword, na=False)]

        if len(result) == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            st.success(f"{len(result)}건 검색")
            st.dataframe(result[["주차장명", "주소", "기본요금"]])

    # 지도 생성
    st.subheader("공영주차장 지도")

    m = folium.Map(
        location=[df["위도"].mean(), df["경도"].mean()],
        zoom_start=12
    )

    for _, row in df.iterrows():

        folium.Marker(
            location=[row["위도"], row["경도"]],
            tooltip=f"""
주소 : {row['주소']}
<br>
요금 : {row['기본요금']}
""",
            popup=f"""
<b>{row['주차장명']}</b><br>
주소 : {row['주소']}<br>
요금 : {row['기본요금']}
"""
        ).add_to(m)

    st_folium(m, width=1200, height=600)
