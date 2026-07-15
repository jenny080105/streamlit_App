import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


# =================================
# 기본 설정
# =================================

st.set_page_config(
    page_title="서울 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)


# =================================
# 디자인
# =================================

st.markdown(
    """
<style>

.title {
    font-size:38px;
    font-weight:800;
    color:#1f4e79;
}

.card {
    background:#f7f9fc;
    padding:20px;
    border-radius:15px;
    text-align:center;
    box-shadow:0 2px 10px #ddd;
}

.card h2 {
    color:#1f4e79;
}

</style>
""",
    unsafe_allow_html=True
)



# =================================
# 제목
# =================================

st.markdown(
    "<div class='title'>🅿️ 서울시 공영주차장 안내 서비스</div>",
    unsafe_allow_html=True
)

st.caption(
    "구와 동을 선택하면 주변 공영주차장 위치와 요금을 확인할 수 있습니다."
)



# =================================
# 파일 업로드
# =================================

uploaded_file = st.file_uploader(
    "📂 공영주차장 CSV 업로드",
    type=["csv"]
)



def load_csv(file):

    for encoding in [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]:

        try:
            file.seek(0)

            return pd.read_csv(
                file,
                encoding=encoding
            )

        except:

            continue


    st.error(
        "CSV 파일을 읽을 수 없습니다."
    )

    st.stop()



if uploaded_file:


    df = load_csv(uploaded_file)



    # =================================
    # 데이터 처리
    # =================================


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


    # 좌표 없는 데이터 제거

    df = df.dropna(
        subset=[
            "위도",
            "경도"
        ]
    )


    # 요금 없는 경우 0 처리

    df["기본 주차 요금"] = (
        df["기본 주차 요금"]
        .fillna(0)
    )


    # ⭐ 중복 주차장 제거

    df = df.drop_duplicates(
        subset=[
            "주차장명",
            "주소",
            "위도",
            "경도"
        ]
    )



    # =================================
    # 구 / 동 생성
    # =================================


    df["구"] = (
        df["주소"]
        .astype(str)
        .str.extract(
            r"(\S+구)"
        )[0]
    )


    df["동"] = (
        df["주소"]
        .astype(str)
        .str.extract(
            r"(\S+동)"
        )[0]
    )



    # =================================
    # 통계
    # =================================


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



    # =================================
    # 사이드바
    # =================================


    st.sidebar.title(
        "📍 검색 조건"
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



    # =================================
    # 필터링
    # =================================


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



    # =================================
    # 지도
    # =================================


    st.subheader(
        "🗺️ 공영주차장 지도"
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

            marker_color = "green"

        else:

            marker_color = "red"



        popup = f"""

<b>{row['주차장명']}</b>
<br><br>

📍 주소<br>
{row['주소']}

<br><br>

💰 기본요금<br>
{row['기본 주차 요금']}원

<br><br>

🚗 주차면수<br>
{row['총 주차면']}면

<br><br>

🅿️ 구분<br>
{row['유무료구분명']}

"""



        folium.Marker(

            location=[

                row["위도"],

                row["경도"]

            ],

            tooltip=row["주차장명"],

            popup=popup,

            icon=folium.Icon(

                color=marker_color,

                icon="info-sign"

            )

        ).add_to(m)



    st_folium(

        m,

        width=1200,

        height=600

    )



    # =================================
    # 결과
    # =================================


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
