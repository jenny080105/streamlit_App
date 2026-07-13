import base64
from io import BytesIO

import streamlit as st
from openai import OpenAI
from PIL import Image

st.set_page_config(
    page_title="SeeEasy",
    page_icon="👁️",
    layout="wide"
)

# OpenAI 클라이언트
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("👁️ SeeEasy")
st.write("시각장애인을 위한 AI 이미지 설명 도우미")

uploaded_file = st.file_uploader(
    "이미지를 업로드하세요",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="업로드한 이미지", use_container_width=True)

    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode()

    if st.button("이미지 설명 생성"):

        with st.spinner("AI가 이미지를 분석하는 중입니다..."):

            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": """
당신은 시각장애인을 돕는 AI입니다.

다음 형식으로 답변하세요.

## 전체 상황

## 중요한 위험 요소

## 사용자가 해야 할 행동

## 3줄 요약

쉬운 단어를 사용하세요.
"""
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{image_base64}"
                            }
                        ]
                    }
                ]
            )

        result = response.output_text

        st.success("분석 완료!")
        st.markdown(result)

        st.session_state["image_description"] = result

if "image_description" in st.session_state:

    st.divider()

    st.subheader("이미지에 대해 질문하기")

    question = st.text_input("질문을 입력하세요")

    if st.button("질문하기"):

        response = client.responses.create(
            model="gpt-4.1",
            input=f"""
다음은 이미지 설명입니다.

{st.session_state['image_description']}

질문:
{question}
"""
        )

        st.write(response.output_text)
