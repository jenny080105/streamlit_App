import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="서울 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)


# -----------------------------
# CSS 디자인
# -----------------------------
st.markdown(
    """
<style>

.main-title {
    font-size:38px;
    font-weight:800;
    color:#1f4e79;
}

.card {
    background:#f5f7fa;
    padding:20px;
    border-radius:15px;
    text-align:center;
    box-shadow:0 2px 8px #ddd;
}

.card h2 {
    color:#1f4e79;
}

</style>
""",
    unsafe_allow_html=True
)



# -----------------------------
# 제목
# -----------------------------
st.markdown(
    "<div class='main-title'>🅿️ 서울시 공영주차장 안내 서비스</div>",
    unsafe_allow_html=True
)

st.caption(
    "주차 위치 · 요금 · 운영 정보를 한눈에 확인하세요."
)



# -----------------------------
# CSV 업로드
# -----------------------------
uploaded_file = st.file_uploader(
    "📂 공영주차장 CSV 업로드",
    type=["csv"]
)



def load_csv(file):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]

    for enc in encodings:

        try:
            file.seek(0)
            return pd.read_csv(
                file,
                encoding=enc
            )

        except:
            pass


    st.error(
        "CSV 파일을 읽을 수 없습니다."
    )

    st.stop()



if uploaded_file:


    df = load_csv(uploaded_file)


    # -----------------------------
    # 데이터 변환
    # -----------------------------

    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )


    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )


    df["기본 주차 요금"] = pd.to_numeric(
        df["기본 주차 요금"],
        errors="coerce"
    )


    df = df.dropna(
        subset=[
            "위도",
            "경도"
        ]
    )


    df["기본 주차 요금"] = (
        df["기본 주차 요금"]
        .fillna(0)
    )



    # -----------------------------
    # 통계
    # -----------------------------

    total = len(df)


    free_count = len(
        df[
            df["유무료구분명"]
            .astype(str)
            .str.contains("무료")
        ]
    )


    paid_count = total - free_count



    c1,c2,c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
<div class="card">
<h2>{total}</h2>
전체 주차장
</div>
""",
            unsafe_allow_html=True
        )



    with c2:

        st.markdown(
            f"""
<div class="card">
<h2>{free_count}</h2>
무료 주차장
</div>
""",
            unsafe_allow_html=True
        )



    with c3:

        st.markdown(
            f"""
<div class="card">
<h2>{paid_count}</h2>
유료 주차장
</div>
""",
            unsafe_allow_html=True
        )



    st.divider()



    # -----------------------------
    # 사이드바
    # -----------------------------

    st.sidebar.title(
        "🔎 검색 조건"
    )


    keyword = st.sidebar.text_input(
        "주소 또는 주차장명"
    )



    # 자치구 추출

    gu_list = sorted(
        df["주소"]
        .astype(str)
        .str.extract(
            r"(서울특별시\s+\S+구)"
        )[0]
        .dropna()
        .str.replace(
            "서울특별시 ",
            ""
        )
        .unique()
    )


    selected_gu = st.sidebar.selectbox(
        "자치구",
        ["전체"] + gu_list
    )



    parking_type = st.sidebar.selectbox(
        "요금 구분",
        [
            "전체",
            "무료",
            "유료"
        ]
    )



    max_fee = st.sidebar.slider(
        "최대 기본요금",
        0,
        int(
            df["기본 주차 요금"]
            .max()
        ),
        5000
    )



    # -----------------------------
    # 필터링
    # -----------------------------

    result = df.copy()



    if keyword:

        result = result[
            df["주소"]
            .astype(str)
            .str.contains(
                keyword,
                na=False
            )
            |
            df["주차장명"]
            .astype(str)
            .str.contains(
                keyword,
                na=False
            )
        ]



    if selected_gu != "전체":

        result = result[
            result["주소"]
            .astype(str)
            .str.contains(
                selected_gu,
                na=False
            )
        ]



    if parking_type == "무료":

        result = result[
            result["유무료구분명"]
            .astype(str)
            .str.contains(
                "무료"
            )
        ]



    elif parking_type == "유료":

        result = result[
            ~result["유무료구분명"]
            .astype(str)
            .str.contains(
                "무료"
            )
        ]



    result = result[
        result["기본 주차 요금"]
        <= max_fee
    ]



    # -----------------------------
    # 지도
    # -----------------------------

    st.subheader(
        "🗺️ 주차장 지도"
    )


    if len(result) == 0:

        st.warning(
            "조건에 맞는 주차장이 없습니다."
        )

        st.stop()



    center = [
        result["위도"].mean(),
        result["경도"].mean()
    ]



    m = folium.Map(
        location=center,
        zoom_start=12
    )



    for _, row in result.iterrows():


        if "무료" in str(row["유무료구분명"]):

            color="green"

        else:

            color="red"



        popup = f"""
        <b>{row['주차장명']}</b><br><br>

        📍 주소<br>
        {row['주소']}<br><br>

        💰 기본요금<br>
        {row['기본 주차 요금']}원<br><br>

        🚗 주차면<br>
        {row['총 주차면']}면<br><br>

        ⏰ 운영시간<br>
        {row['평일 운영 시작시각(HHMM)']}
        ~
        {row['평일 운영 종료시각(HHMM)']}
        """



        folium.Marker(

            location=[
                row["위도"],
                row["경도"]
            ],

            tooltip=row["주차장명"],

            popup=popup,

            icon=folium.Icon(
                color=color
            )

        ).add_to(m)



    st_folium(
        m,
        width=1200,
        height=600
    )



    # -----------------------------
    # 결과표
    # -----------------------------

    st.subheader(
        f"📋 검색 결과 ({len(result)}개)"
    )


    st.dataframe(

        result[
            [
                "주차장명",
                "주소",
                "유무료구분명",
                "기본 주차 요금",
                "총 주차면"
            ]
        ],

        use_container_width=True

    )



else:


    st.info(
        "CSV 파일을 업로드하면 서비스가 시작됩니다."
    )
