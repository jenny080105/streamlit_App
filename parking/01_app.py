import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


st.set_page_config(
    page_title="서울 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)


# -----------------------------
# 디자인
# -----------------------------
st.markdown("""
<style>

.title {
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

</style>
""", unsafe_allow_html=True)



# -----------------------------
# 제목
# -----------------------------
st.markdown(
    "<div class='title'>🅿️ 서울시 공영주차장 안내 서비스</div>",
    unsafe_allow_html=True
)

st.caption(
    "구와 동을 선택하면 주변 공영주차장 정보를 확인할 수 있습니다."
)



# -----------------------------
# 파일 업로드
# -----------------------------
file = st.file_uploader(
    "📂 공영주차장 CSV 업로드",
    type=["csv"]
)



def load_csv(file):

    for enc in [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]:

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



if file:


    df = load_csv(file)



    # -----------------------------
    # 데이터 처리
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
    ).fillna(0)



    df = df.dropna(
        subset=[
            "위도",
            "경도"
        ]
    )



    # 구 추출

    df["구"] = (
        df["주소"]
        .astype(str)
        .str.extract(
            r"(\S+구)"
        )[0]
    )



    # 동 추출

    df["동"] = (
        df["주소"]
        .astype(str)
        .str.extract(
            r"(\S+동)"
        )[0]
    )



    # -----------------------------
    # 통계 카드
    # -----------------------------

    total = len(df)


    free = len(
        df[
            df["유무료구분명"]
            .astype(str)
            .str.contains("무료")
        ]
    )


    paid = total-free



    a,b,c = st.columns(3)


    with a:

        st.markdown(
            f"""
            <div class="card">
            <h2>{total}</h2>
            전체 주차장
            </div>
            """,
            unsafe_allow_html=True
        )


    with b:

        st.markdown(
            f"""
            <div class="card">
            <h2>{free}</h2>
            무료
            </div>
            """,
            unsafe_allow_html=True
        )



    with c:

        st.markdown(
            f"""
            <div class="card">
            <h2>{paid}</h2>
            유료
            </div>
            """,
            unsafe_allow_html=True
        )



    st.divider()



    # -----------------------------
    # 사이드바
    # -----------------------------

    st.sidebar.title(
        "📍 지역 선택"
    )


    gu_list = sorted(
        df["구"]
        .dropna()
        .unique()
    )


    selected_gu = st.sidebar.selectbox(
        "구 선택",
        ["전체"] + list(gu_list)
    )



    temp = df.copy()


    if selected_gu != "전체":

        temp = temp[
            temp["구"] == selected_gu
        ]



    dong_list = sorted(
        temp["동"]
        .dropna()
        .unique()
    )



    selected_dong = st.sidebar.selectbox(
        "동 선택",
        ["전체"] + list(dong_list)
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
    # 필터 적용
    # -----------------------------

    result = df.copy()



    if selected_gu != "전체":

        result = result[
            result["구"] == selected_gu
        ]



    if selected_dong != "전체":

        result = result[
            result["동"] == selected_dong
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
        zoom_start=14
    )



    for _, row in result.iterrows():


        if "무료" in str(row["유무료구분명"]):

            color="green"

        else:

            color="red"



        popup=f"""

        <b>{row['주차장명']}</b>
        <br><br>

        📍 주소 :
        {row['주소']}

        <br><br>

        💰 기본요금 :
        {row['기본 주차 요금']}원

        <br><br>

        🚗 주차면 :
        {row['총 주차면']}면

        <br><br>

        ⏰ 운영 :
        {row['평일 운영 시작시각(HHMM)']}
        -
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
    # 결과
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
        "CSV 파일을 업로드해주세요."
    )
