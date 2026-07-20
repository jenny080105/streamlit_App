import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

from wordcloud import WordCloud
from googleapiclient.discovery import build

from utils import (
    get_video_id,
    get_video_info,
    get_comments,
    create_wordcloud,
    get_word_frequency,
)

from sentiment import analyze_sentiments

st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📺",
    layout="wide"
)

st.title("📺 YouTube 댓글 분석기")

st.markdown(
"""
유튜브 영상의 댓글을 분석합니다.

기능

- 댓글 수집
- 시간대 분석
- 감성 분석
- 워드클라우드
- 자주 등장한 단어
"""
)

##############################################
# Sidebar
##############################################

with st.sidebar:

    st.header("설정")

    api_key = st.text_input(
        "YouTube API Key",
        type="password"
    )

    url = st.text_input(
        "YouTube URL"
    )

    max_comments = st.slider(
        "댓글 개수",
        50,
        1000,
        300,
        50
    )

    analyze = st.button("분석 시작")

##############################################

if analyze:

    if api_key == "":
        st.error("API Key를 입력하세요.")
        st.stop()

    if url == "":
        st.error("URL을 입력하세요.")
        st.stop()

    video_id = get_video_id(url)

    if video_id is None:
        st.error("올바른 URL이 아닙니다.")
        st.stop()

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    with st.spinner("영상 정보 가져오는 중..."):

        video = get_video_info(
            youtube,
            video_id
        )

    st.subheader(video["title"])

    st.video(url)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "조회수",
        f"{video['views']:,}"
    )

    col2.metric(
        "좋아요",
        f"{video['likes']:,}"
    )

    col3.metric(
        "댓글 수",
        f"{video['commentCount']:,}"
    )

    st.divider()

    progress = st.progress(0)

    with st.spinner("댓글 수집 중..."):

        comments = get_comments(
            youtube,
            video_id,
            max_comments,
            progress
        )

    progress.empty()

    if len(comments) == 0:

        st.warning("댓글이 없습니다.")

        st.stop()

    df = pd.DataFrame(comments)

    st.success(f"{len(df)}개의 댓글을 분석합니다.")

    ###########################################
    # 댓글 데이터
    ###########################################

    st.subheader("댓글")

    st.dataframe(
        df[
            [
                "author",
                "text",
                "likes",
                "published"
            ]
        ],
        use_container_width=True
    )

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "youtube_comments.csv",
        "text/csv"
    )

    ###########################################
    # 시간 분석
    ###########################################

    st.divider()

    st.subheader("댓글 작성 추이")

    df["published"] = pd.to_datetime(df["published"])

    if len(df) < 300:

        df["time"] = df["published"].dt.date

    else:

        df["time"] = df["published"].dt.floor("H")

    graph = (
        df.groupby("time")
        .size()
        .reset_index(name="count")
    )

    fig = px.line(
        graph,
        x="time",
        y="count",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    ###########################################
    # 감성 분석
    ###########################################

    st.divider()

    st.subheader("감성 분석")

    with st.spinner("BERT 분석 중..."):

        sentiments = analyze_sentiments(
            df["text"].tolist()
        )

    df["sentiment"] = sentiments

    result = (
        df["sentiment"]
        .value_counts()
        .reset_index()
    )

    result.columns = [
        "감정",
        "개수"
    ]

    fig = px.pie(
        result,
        names="감정",
        values="개수",
        hole=.4
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    ###########################################
    # 워드클라우드
    ###########################################

    st.divider()

    st.subheader("워드클라우드")

    wc = create_wordcloud(
        df["text"].tolist()
    )

    fig, ax = plt.subplots(figsize=(10,5))

    ax.imshow(wc)

    ax.axis("off")

    st.pyplot(fig)

    ###########################################
    # 단어 빈도
    ###########################################

    st.divider()

    st.subheader("TOP20 단어")

    words = get_word_frequency(
        df["text"].tolist()
    )

    word_df = pd.DataFrame(
        words.items(),
        columns=["단어","빈도"]
    ).sort_values(
        "빈도",
        ascending=False
    ).head(20)

    fig = px.bar(
        word_df,
        x="단어",
        y="빈도"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
  import re

from collections import Counter

from kiwipiepy import Kiwi

from wordcloud import WordCloud

kiwi = Kiwi()

############################################
# 영상 ID 추출
############################################

def get_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"shorts/([^?]+)"
    ]

    for pattern in patterns:

        m = re.search(pattern, url)

        if m:
            return m.group(1)

    return None


############################################
# 영상 정보
############################################

def get_video_info(youtube, video_id):

    response = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    ).execute()

    item = response["items"][0]

    snippet = item["snippet"]
    stat = item["statistics"]

    return {

        "title": snippet["title"],

        "views": int(
            stat.get("viewCount",0)
        ),

        "likes": int(
            stat.get("likeCount",0)
        ),

        "commentCount": int(
            stat.get("commentCount",0)
        )

    }


############################################
# 댓글 수집
############################################

def get_comments(
    youtube,
    video_id,
    max_comments,
    progress
):

    comments = []

    token = None

    while True:

        request = youtube.commentThreads().list(

            part="snippet",

            videoId=video_id,

            maxResults=100,

            pageToken=token,

            textFormat="plainText",

            order="relevance"

        )

        response = request.execute()

        for item in response["items"]:

            comment = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({

                "author":
                comment["authorDisplayName"],

                "text":
                comment["textDisplay"],

                "likes":
                comment["likeCount"],

                "published":
                comment["publishedAt"]

            })

            progress.progress(
                min(
                    len(comments)/max_comments,
                    1.0
                )
            )

            if len(comments) >= max_comments:
                return comments

        token = response.get("nextPageToken")

        if token is None:
            break

    return comments


############################################
# 불용어
############################################

STOPWORDS = {

"ㅋㅋ",
"ㅎㅎ",
"진짜",
"너무",
"정말",
"그냥",
"영상",
"오늘",
"이번",
"이거",
"저거",
"그거",
"근데",
"때문",
"사람",
"생각",
"하나",
"이제",
"항상",
"우리",
"여기",
"저기",
"뭔가",
"가장",
"입니다",
"합니다",
"있는",
"없는",
"같은"

}


############################################
# 명사 추출
############################################

def extract_nouns(texts):

    nouns = []

    for text in texts:

        try:

            tokens = kiwi.tokenize(text)

            for token in tokens:

                if token.tag.startswith("N"):

                    word = token.form

                    if len(word) < 2:
                        continue

                    if word in STOPWORDS:
                        continue

                    nouns.append(word)

        except:
            pass

    return nouns


############################################
# 단어 빈도
############################################

def get_word_frequency(texts):

    nouns = extract_nouns(texts)

    return Counter(nouns)


############################################
# 워드클라우드
############################################

def create_wordcloud(texts):

    freq = get_word_frequency(texts)

    wc = WordCloud(

        font_path="NanumGothic.ttf",

        background_color="white",

        width=1200,

        height=700

    ).generate_from_frequencies(freq)

    return wc
  from transformers import pipeline
import streamlit as st

####################################################
# 모델 캐시
####################################################

@st.cache_resource
def load_model():

    model = pipeline(
        "sentiment-analysis",
        model="beomi/KcELECTRA-base-v2022",
        tokenizer="beomi/KcELECTRA-base-v2022",
        truncation=True
    )

    return model


####################################################
# 댓글 감성 분석
####################################################

def analyze_sentiments(texts):

    model = load_model()

    results = []

    batch_size = 32

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i+batch_size]

        predicts = model(batch)

        for p in predicts:

            label = p["label"]
            score = p["score"]

            # label 이름이 모델마다 다를 수 있음
            positive = (
                label.upper() == "POSITIVE"
                or label == "1"
                or "POS" in label.upper()
            )

            if positive:

                if score >= 0.75:
                    results.append("😊 긍정")
                else:
                    results.append("😐 중립")

            else:

                if score >= 0.75:
                    results.append("😡 부정")
                else:
                    results.append("😐 중립")

    return results
