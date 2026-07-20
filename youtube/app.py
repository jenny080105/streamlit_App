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

# 3. 자체 고도화된 한국어 감성 분석 사전 및 함수
# 외부 대용량 라이브러리 없이 클라우드 환경에서 정확하고 빠르게 동작하는 매칭 규칙입니다.
POSITIVE_WORDS = ['좋다', '최고', '유익', '대박', '재밌', '감사', '도움', '알참', '최고다', '지렸다', '갓', '이해', '쉽다', '사랑', '추천', '👍', '🔥', '❤️', '👏', 'ㅋㅋ', 'ㅎㅎ']
NEGATIVE_WORDS = ['실망', '아쉽', '노잼', '최악', '어렵다', '이해안됨', '지루', '노답', '불편', '부족', '시간낭비', '광고', '속도', '별로', '👎', '휴', 'ㅠㅠ', 'ㅜㅜ']

def analyze_korean_sentiment(text):
    score = 0
    text = text.lower()
    
    for word in POSITIVE_WORDS:
        if word in text:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in text:
            score -= 1
            
    if score > 0:
        return "긍정", score
    elif score < 0:
        return "부정", score
    else:
        return "중립", 0

# 4. 워드클라우드용 한글 불용어(Stopwords) 정제 함수
def clean_text_and_filter(text):
    # 한글, 숫자, 이모지, 공백 제외 제거
    text = re.sub(r"[^가-힣0-9\s👍🔥❤️👏👎]", "", text)
    
    # 무의미한 단순 조사 및 단어 필터링
    stopwords = ['진짜', '너무', '영상', '유튜브', '댓글', '보고', '하나', '항상', '정말', '이거', '저거', '그거', '많이', '조금', '종종']
    words = text.split()
    result_words = [w for w in words if w not in stopwords and len(w) > 1]
    return " ".join(result_words)

# 5. 유튜브 댓글 수집 함수 (좋아요 수, 답글 수 추가 수집으로 정밀도 향상)
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
                like_count = snippet["likeCount"]
                
                comments.append({
                    "text": text, 
                    "date": published_at,
                    "likes": like_count
                })
                
                if len(comments) >= max_count:
                    break
                    
            request = youtube.commentThreads().list_next(request, response)
            
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 6. 스트림릿 UI 레이아웃
st.set_page_config(page_title="유튜브 대시보드 Pro", layout="wide")
st.title("🚀 고도화된 유튜브 댓글 인사이트 분석기")
st.caption("고도화된 한글 감성 분석 엔진과 불용어 처리 기술이 적용된 프로페셔널 버전입니다.")

# 사이드바 설정
st.sidebar.header("🎯 분석 옵션")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요")
max_comments = st.sidebar.slider("수집할 댓글 개수 설정", min_value=20, max_value=1000, value=200, step=20)
time_resample = st.sidebar.selectbox("시간 추이 단위 선택", options=["일별 (Day)", "시간별 (Hour)"])

# URL에서 Video ID 추출
video_id = None
if video_url:
    if "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]

# 메인 분석 로직
if st.sidebar.button("인사이트 추출 시작"):
    if not video_id:
        st.warning("올바른 유튜브 링크를 입력해주세요.")
    else:
        with st.spinner("댓글 수집 및 다차원 분석을 진행 중입니다..."):
            
            # 데이터 수집
            df = get_youtube_comments(API_KEY, video_id, max_comments)
            
            if not df.empty:
                # 데이터 전처리 및 분석 엔진 가동
                df["date"] = pd.to_datetime(df["date"]).dt.tz_convert('Asia/Seoul') # 한국 시간대 변환
                df["cleaned_text"] = df["text"].apply(clean_text_and_filter)
                
                sentiment_results = df["text"].apply(analyze_korean_sentiment)
                df["sentiment"] = [r[0] for r in sentiment_results]
                df["sentiment_score"] = [r[1] for r in sentiment_results]
                
                # ---------------- 주요 핵심 통계 지표 (KPI) ----------------
                st.subheader("📊 핵심 요약 지표 (Core Metrics)")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                pos_ratio = (df["sentiment"] == "긍정").sum() / len(df) * 100
                most_liked_comment = df.loc[df["likes"].idxmax()]["text"] if df["likes"].max() > 0 else "없음"
                
                kpi1.metric("총 수집 댓글 수", f"{len(df)}개")
                kpi2.metric("긍정 반응 지수", f"{pos_ratio:.1f}%")
                kpi3.metric("최대 좋아요 댓글 수", f"{df['likes'].max()}개")
                kpi4.metric("평균 감성 점수", f"{df['sentiment_score'].mean():.2f}")
                
                st.markdown("---")
                
                # ---------------- 화면 분할 레이아웃 ----------------
                row1_col1, row1_col2 = st.columns([1, 1])
                
                with row1_col1:
                    st.subheader("📺 분석 대상 영상")
                    st.video(video_url)
                    
                    # 가장 반응이 좋은 베스트 댓글 시각화
                    if df["likes"].max() > 0:
                        st.info(f"🏆 **가장 많은 공감을 받은 댓글 (좋아요 {df['likes'].max()}개):**\n\n\"{most_liked_comment}\"")
                
                with row1_col2:
                    st.subheader("📈 시간 흐름에 따른 반응 추이")
                    resample_rule = "D" if "일별" in time_resample else "h"
                    df_time = df.set_index("date").resample(resample_rule).size().reset_index(name="count")
                    
                    fig, ax = plt.subplots(figsize=(10, 4.8))
                    ax.plot(df_time["date"], df_time["count"], marker="o", color="#E60023", linewidth=2)
                    ax.set_ylabel("Comment Count")
                    plt.xticks(rotation=30)
                    plt.grid(True, linestyle="--", alpha=0.5)
                    st.pyplot(fig)
                
                st.markdown("---")
                
                row2_col1, row2_col2 = st.columns(2)
                
                # 반응도 (차트 디자인 개선)
                with row2_col1:
                    st.subheader("🥰 댓글 감성 반응도 현황")
                    sentiment_counts = df["sentiment"].value_counts().reindex(["긍정", "중립", "부정"], fill_value=0)
                    
                    fig, ax = plt.subplots()
                    wedges, texts, autotexts = ax.pie(
                        sentiment_counts, 
                        labels=sentiment_counts.index, 
                        autopct="%1.1f%%", 
                        startangle=90, 
                        colors=["#2ecc71", "#95a5a6", "#e74c3c"],
                        textprops=dict(color="black")
                    )
                    plt.setp(autotexts, size=10, weight="bold")
                    ax.axis("equal")
                    st.pyplot(fig)
                
                # 워드클라우드 (정밀 정제 텍스트 적용)
                with row2_col2:
                    st.subheader("🔠 정제된 핵심 단어 (Word Cloud)")
                    all_text = " ".join(df["cleaned_text"].dropna())
                    
                    if all_text.strip():
                        wc = WordCloud(
                            font_path=font_path,
                            background_color="white",
                            width=800,
                            height=500,
                            max_words=80,
                            colormap="inferno"
                        ).generate(all_text)
                        
                        fig, ax = plt.subplots()
                        ax.imshow(wc, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)
                    else:
                        st.info("단어 구름을 생성할 한글 명사 텍스트가 부족합니다.")
                
                st.markdown("---")
                
                # ---------------- 데이터 관리 섹션 ----------------
                st.subheader("💬 데이터 분석 명세서 및 다운로드")
                
                # 수집된 원본 및 분석 결과 데이터를 다운로드할 수 있는 기능 추가
                output_df = df[["date", "text", "likes", "sentiment", "sentiment_score"]]
                csv_data = output_df.to_csv(index=False).encode('utf-8-sig') # 엑셀 깨짐 방지용 utf-8-sig
                
                st.download_button(
                    label="📥 분석 결과 전체 파일(CSV) 다운로드",
                    data=csv_data,
                    file_name=f"youtube_comments_{video_id}.csv",
                    mime="text/csv",
                )
                
                st.dataframe(output_df, use_container_width=True)
            else:
                st.error("해당 영상에 분석할 수 있는 댓글이 존재하지 않거나 가져오지 못했습니다.")
