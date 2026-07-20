import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob
import re
import urllib.request

# 1. 시스템 내부에 저장된 API Key 가져오기
# .streamlit/secrets.toml 파일 또는 Streamlit Cloud 대시보드 Secrets 설정을 참고합니다.
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("⚠️ 시스템에 YOUTUBE_API_KEY 설정이 누락되었습니다. 관리자 설정을 확인해 주세요.")
    st.stop()

# 2. 한글 폰트 설정 (Streamlit Cloud 환경 대응)
@st.cache_data
def load_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    font_path = "NanumGothic.ttf"
    urllib.request.urlretrieve(font_url, font_path)
    return font_path

try:
    font_path = load_font()
except Exception:
    font_path = None

# 3. 유튜브 댓글 수집 함수
def get_youtube_comments(api_key, video_id, max_count):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_count, 100),
            textFormat="plainText"
        )
        
        while request and len(comments) < max_count:
            response = request.execute()
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet["textDisplay"]
                published_at = snippet["publishedAt"]
                comments.append({"text": text, "date": published_at})
                
                if len(comments) >= max_count:
                    break
                    
            request = youtube.commentThreads().list_next(request, response)
            
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 4. 데이터 전처리 및 분석 함수
def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "긍정"
    elif analysis.sentiment.polarity < 0:
        return "부정"
    else:
        return "중립"

def clean_text(text):
    return re.sub(r"[^가-힣\s]", "", text)

# 5. 스트림릿 UI 레이아웃
st.title("📊 유튜브 댓글 분석기")
st.caption("유튜브 영상의 댓글을 수집하여 작성 추이, 반응도, 워드클라우드를 분석합니다.")

# 사이드바 설정 (API 입력란 제거)
st.sidebar.header("분석 옵션 설정")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요")
max_comments = st.sidebar.slider("수집할 댓글 개수 선택", min_value=10, max_value=500, value=100, step=10)

# URL에서 Video ID 추출
video_id = None
if video_url:
    if "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]

# 메인 분석 로직
if st.sidebar.button("분석 시작"):
    if not video_id:
        st.warning("올바른 유튜브 링크를 입력해주세요.")
    else:
        with st.spinner("댓글을 수집하고 분석하는 중입니다..."):
            # 영상 출력
            st.subheader("📺 분석 대상 영상")
            st.video(video_url)
            
            # 내부에 설정된 API_KEY 변수를 넣어 호출
            df = get_youtube_comments(API_KEY, video_id, max_comments)
            
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df["cleaned_text"] = df["text"].apply(clean_text)
                df["sentiment"] = df["text"].apply(analyze_sentiment)
                
                st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다.")
                
                # 레이아웃 분할
                col1, col2 = st.columns(2)
                
                # 1. 시간대별 댓글 작성 추이
                with col1:
                    st.subheader("📈 시간대별 댓글 작성 추이")
                    df_time = df.set_index("date").resample("D").size().reset_index(name="count")
                    
                    fig, ax = plt.subplots()
                    ax.plot(df_time["date"], df_time["count"], marker="o", color="#1f77b4")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Comment Count")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                
                # 2. 댓글 반응도 (긍정/부정/중립)
                with col2:
                    st.subheader("🥰 댓글 반응도 상황")
                    sentiment_counts = df["sentiment"].value_counts()
                    
                    fig, ax = plt.subplots()
                    ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct="%1.1f%%", startangle=90, 
                           colors=["#6baed6", "#9ecae1", "#c6dbef"])
                    ax.axis("equal")
                    st.pyplot(fig)
                
                # 3. 한글 워드클라우드
                st.subheader("🔠 댓글 한글 워드클라우드")
                all_text = " ".join(df["cleaned_text"].dropna())
                
                if all_text.strip():
                    wc = WordCloud(
                        font_path=font_path,
                        background_color="white",
                        width=800,
                        height=400,
                        max_words=100
                    ).generate(all_text)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)
                else:
                    st.info("워드클라우드를 생성할 만큼의 한글 텍스트가 댓글에 존재하지 않습니다.")
                    
                # 데이터프레임 미리보기
                st.subheader("💬 수집된 댓글 데이터 목록")
                st.dataframe(df[["date", "text", "sentiment"]], use_container_width=True)
