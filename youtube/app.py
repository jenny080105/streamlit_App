import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
import urllib.request

# 1. 시스템 내부에 저장된 API Key 가져오기
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

# 3. 한국어 감성 분석 사전 및 함수
POSITIVE_WORDS = ['좋다', '최고', '유익', '대박', '재밌', '감사', '도움', '알참', '최고다', '지렸다', '갓', '이해', '쉽다', '사랑', '추천', '👍', '🔥', '❤️', '👏', 'ㅋㅋ', 'ㅎㅎ']
NEGATIVE_WORDS = ['실망', '아쉽', '노잼', '최악', '어렵다', '이해안됨', '지루', '노답', '불편', '부족', '시간낭비', '광고', '속도', '별로', '👎', '휴', 'ㅠㅠ', 'ㅜㅜ']

def analyze_korean_sentiment(text):
    score = 0
    text = text.lower()
    for word in POSITIVE_WORDS:
        if word in text: score += 1
    for word in NEGATIVE_WORDS:
        if word in text: score -= 1
    if score > 0: return "긍정", score
    elif score < 0: return "부정", score
    else: return "중립", 0

# 4. 워드클라우드용 한글 불용어(Stopwords) 정제 함수
def clean_text_and_filter(text):
    text = re.sub(r"[^가-힣0-9\s👍🔥❤️👏👎]", "", text)
    stopwords = ['진짜', '너무', '영상', '유튜브', '댓글', '보고', '하나', '항상', '정말', '이거', '저거', '그거', '많이', '조금', '종종']
    words = text.split()
    return " ".join([w for w in words if w not in stopwords and len(w) > 1])

# 5. 영상의 '전체 댓글'을 제한 없이 끝까지 수집하는 함수 (💡 핵심 수정 부분)
def get_all_youtube_comments(api_key, video_id):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,  # 한 번 요청할 때 가져올 수 있는 최대 단위
        textFormat="plainText"
    )
    
    # 실시간 수집 현황을 화면에 찍어주기 위한 빈 공간 생성
    status_text = st.empty()
    
    try:
        while request:
            response = request.execute()
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": snippet["textDisplay"], 
                    "date": snippet["publishedAt"],
                    "likes": snippet["likeCount"]
                })
            
            # 2026년부터 과거로 거슬러 올라가며 실시간으로 누적 개수를 보여줍니다.
            status_text.text(f"📥 현재까지 과거 데이터를 탈탈 털어 {len(comments)}개의 댓글을 수집했습니다...")
            
            # 다음 페이지 토큰을 받아와 과거 데이터로 계속 진입 (더 없으면 None이 되어 멈춤)
            request = youtube.commentThreads().list_next(request, response)
            
        status_text.empty()  # 수집이 완전히 끝나면 문구 지우기
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 6. 스트림릿 UI 레이아웃
st.set_page_config(page_title="유튜브 전체 분석기 Pro", layout="wide")
st.title("🚀 유튜브 전체 댓글 다차원 분석기")
st.caption("영상의 첫 업로드 순간부터 현재까지 달린 모든 댓글을 추적하여 전체 흐름을 시각화합니다.")

# 사이드바 설정 (개수 제한 슬라이더 제거)
st.sidebar.header("🎯 분석 옵션")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요")
time_resample = st.sidebar.selectbox("시간 추이 단위 선택", options=["월별 (Month)", "일별 (Day)"])

# URL에서 Video ID 추출
video_id = None
if video_url:
    if "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]

# 메인 분석 로직
if st.sidebar.button("전체 인사이트 추출 시작"):
    if not video_id:
        st.warning("올바른 유튜브 링크를 입력해주세요.")
    else:
        with st.spinner("6년 전부터 현재까지의 전체 댓글을 수집하고 있습니다. 잠시만 기다려주세요..."):
            
            # 전체 댓글 수집 함수 호출 (max_comments 매개변수 제거됨)
            df = get_all_youtube_comments(API_KEY, video_id)
            
            if not df.empty:
                # 데이터 전처리 및 분석 엔진 가동
                df["date"] = pd.to_datetime(df["date"]).dt.tz_convert('Asia/Seoul')  # 한국 시간대 변환
                df["cleaned_text"] = df["text"].apply(clean_text_and_filter)
                
                sentiment_results = df["text"].apply(analyze_korean_sentiment)
                df["sentiment"] = [r[0] for r in sentiment_results]
                df["sentiment_score"] = [r[1] for r in sentiment_results]
                
                # ---------------- 주요 핵심 통계 지표 (KPI) ----------------
                st.subheader("📊 핵심 요약 지표 (Core Metrics)")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                pos_ratio = (df["sentiment"] == "긍정").sum() / len(df) * 100
                
                kpi1.metric("전체 누적 댓글 수", f"{len(df)}개")
                kpi2.metric("통합 긍정 반응 지수", f"{pos_ratio:.1f}%")
                kpi3.metric("역대 최고 공감 댓글 (좋아요)", f"{df['likes'].max()}개")
                kpi4.metric("평균 감성 점수", f"{df['sentiment_score'].mean():.2f}")
                
                st.markdown("---")
                
                # ---------------- 화면 분할 레이아웃 ----------------
                row1_col1, row1_col2 = st.columns([1, 1])
                
                with row1_col1:
                    st.subheader("📺 분석 대상 영상")
                    st.video(video_url)
                    
                    if df["likes"].max() > 0:
                        most_liked_comment = df.loc[df["likes"].idxmax()]["text"]
                        st.info(f"🏆 **역대 최고 인기 댓글 (좋아요 {df['likes'].max()}개):**\n\n\"{most_liked_comment}\"")
                
                with row1_col2:
                    st.subheader("📈 6년간의 전체 댓글 작성 흐름")
                    # 6년 기간을 커버하기 위해 '월별(ME)' 정렬을 추천합니다.
                    resample_rule = "ME" if "월별" in time_resample else "D"
                    df_time = df.set_index("date").resample(resample_rule).size().reset_index(name="count")
                    
                    fig, ax = plt.subplots(figsize=(10, 4.8))
                    ax.plot(df_time["date"], df_time["count"], color="#E60023", linewidth=2)
                    ax.set_ylabel("Comment Count")
                    plt.xticks(rotation=30)
                    plt.grid(True, linestyle="--", alpha=0.5)
                    st.pyplot(fig)
                
                st.markdown("---")
                
                row2_col1, row2_col2 = st.columns(2)
                
                # 반응도
                with row2_col1:
                    st.subheader("🥰 전체 댓글 감성 반응도")
                    sentiment_counts = df["sentiment"].value_counts().reindex(["긍정", "중립", "부정"], fill_value=0)
                    
                    fig, ax = plt.subplots()
                    wedges, texts, autotexts = ax.pie(
                        sentiment_counts, labels=sentiment_counts.index, autopct="%1.1f%%", startangle=90, 
                        colors=["#2ecc71", "#95a5a6", "#e74c3c"]
                    )
                    plt.setp(autotexts, size=10, weight="bold")
                    ax.axis("equal")
                    st.pyplot(fig)
                
                # 워드클라우드
                with row2_col2:
                    st.subheader("🔠 역대 핵심 키워드 (Word Cloud)")
                    all_text = " ".join(df["cleaned_text"].dropna())
                    
                    if all_text.strip():
                        wc = WordCloud(
                            font_path=font_path, background_color="white",
                            width=800, height=500, max_words=80, colormap="inferno"
                        ).generate(all_text)
                        
                        fig, ax = plt.subplots()
                        ax.imshow(wc, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)
                    else:
                        st.info("단어 구름을 생성할 텍스트가 부족합니다.")
                
                st.markdown("---")
                
                # ---------------- 데이터 관리 섹션 ----------------
                st.subheader("💬 데이터 명세서 및 다운로드")
                output_df = df[["date", "text", "likes", "sentiment", "sentiment_score"]]
                csv_data = output_df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="📥 전체 데이터 파일(CSV) 다운로드",
                    data=csv_data,
                    file_name=f"youtube_all_comments_{video_id}.csv",
                    mime="text/csv",
                )
                st.dataframe(output_df, use_container_width=True)
            else:
                st.error("해당 영상에 분석할 수 있는 댓글이 존재하지 않습니다.")
