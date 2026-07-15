import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


# ==============================
# 설정
# ==============================

st.set_page_config(
    page_title="서울 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)


# ==============================
# 디자인
# ==============================

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

</style>
""",
    unsafe_allow_html=True
)



st.markdown(
    "<div class='title'>🅿️ 서울시 공영주차장 안내 서비스</div>",
    unsafe_allow_html=True
)

st.caption(
    "구와 동을 선택하여 주변 공영주차장 위치와 요금을 확인하세요."
)



# ==============================
# CSV 읽기
# ==============================

file = st.file_uploader(
    "📂 공영주차장 CSV 업로드",
    type=["csv"]
)


def read_csv(file):

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
            continue


    st.error(
        "CSV 읽기 실패"
    )

    st.stop()



if file:


    df = read_csv(file)



    # ==============================
    # 데이터 정리
    # ==============================


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



    # 좌표 없는 데이터 제거

    df = df.dropna(
        subset=[
            "위도",
            "경도"
        ]
    )



    # ⭐ 주소 정규화

    df["주소"] = (
        df["주소"]
        .astype(str)
        .str.replace(
            " ",
            "",
            regex=False
        )
        .str.strip()
    )



    # ⭐ 주차장명 정리

    df["주차장명"] = (
        df["주차장명"]
        .astype(str)
        .str.strip()
    )



    # ⭐ 강력한 중복 제거

    df = df.drop_duplicates(
        subset=[
            "주차장명",
            "주소"
        ],
        keep="first"
    )



    # ==============================
    # 구 / 동 생성
    # ==============================


    df["구"] = (
        df["주소"]
        .str.extract(
            r"(서울특별시)?(\S+구)"
        )[1]
    )


    df["동"] = (
        df["주소"]
        .str.extract(
            r"(\S+동)"
        )[0]
    )



    # ==============================
    # 통계
    # ==============================


    total = len(df)


    free = len(
        df[
            df["유무료구분명"]
            .astype(str)
            .str.contains(
                "무료"
            )
        ]
    )


    paid = total - free



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



    # ==============================
    # 사이드바
    # ==============================


    st.sidebar.header(
        "📍 지역 선택"
    )



    gu_list = sorted(
        df["구"]
        .dropna()
        .unique()
    )


    selected_gu = st.sidebar.selectbox(
        "구",
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
        "동",
        ["전체"] + list(dong_list)
    )



    fee_type = st.sidebar.selectbox(
        "요금",
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



    # ==============================
    # 필터
    # ==============================


    result = df.copy()



    if selected_gu != "전체":

        result = result[
            result["구"] == selected_gu
        ]



    if selected_dong != "전체":

        result = result[
            result["동"] == selected_dong
        ]



    if fee_type == "무료":

        result = result[
            result["유무료구분명"]
            .astype(str)
            .str.contains(
                "무료"
            )
        ]


    elif fee_type == "유료":

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



    # ⭐ 최종 중복 제거

    result = result.drop_duplicates(
        subset=[
            "주차장명",
            "주소"
        ]
    )



    # ==============================
    # 지도
    # ==============================


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


        color = (
            "green"
            if "무료"
            in str(row["유무료구분명"])
            else
            "red"
        )


        popup = f"""

<b>{row['주차장명']}</b>

<br><br>

📍 주소<br>
{row['주소']}

<br><br>

💰 기본요금<br>
{row['기본 주차 요금']}원

<br><br>

🚗 주차면<br>
{row['총 주차면']}면

"""



        folium.Marker(

            [
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



    # ==============================
    # 결과
    # ==============================


    st.subheader(
        f"📋 검색 결과 {len(result)}개"
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
