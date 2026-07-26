import streamlit as st
from google import genai
from gtts import gTTS
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="사진 설명 도우미", page_icon="📷")

st.title("📷 사진 설명 도우미")
st.write("사진을 찍거나 업로드하면 AI가 장면을 설명해줍니다.")

api_key = st.secrets.get("GOOGLE_API_KEY", None)

if not api_key:
    st.error("API 키가 설정되지 않았습니다. secrets에 GOOGLE_API_KEY를 추가해주세요.")
    st.stop()

client = genai.Client(api_key=api_key)

input_method = st.radio("사진 입력 방법을 선택하세요", ["카메라로 촬영", "파일 업로드"])

image_file = None
if input_method == "카메라로 촬영":
    image_file = st.camera_input("사진을 찍어주세요")
else:
    image_file = st.file_uploader("사진 파일을 선택하세요", type=["jpg", "jpeg", "png"])


def analyze_image(image: Image.Image) -> str:
    prompt = (
        "이 사진을 시각장애인에게 설명한다고 생각하고 한국어로 설명해줘. "
        "다음 순서를 지켜줘: "
        "1) 즉각적인 위험이나 장애물이 있다면 가장 먼저 말할 것 "
        "2) 그다음 눈에 띄는 텍스트(표지판, 안내문 등)가 있다면 읽어줄 것 "
        "3) 마지막으로 전반적인 장면을 간단히 설명할 것. "
        "불필요한 수식어 없이 간결하고 명확한 문장으로 작성해줘."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image],
    )
    return response.text


def text_to_speech(text: str) -> BytesIO:
    tts = gTTS(text=text, lang="ko")
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer


if image_file is not None:
    st.image(image_file, caption="입력된 사진", use_container_width=True)

    if st.button("설명 듣기"):
        with st.spinner("사진을 분석하는 중..."):
            image = Image.open(image_file)
            description = analyze_image(image)

        st.subheader("설명 결과")
        st.write(description)

        with st.spinner("음성으로 변환하는 중..."):
            audio = text_to_speech(description)

        st.audio(audio, format="audio/mp3")
