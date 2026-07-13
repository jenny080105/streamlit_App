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

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("👁️ SeeEasy")
st.subheader("AI 이미지 설명 도우미")

uploaded = st.file_uploader(
    "사진을 업로드하세요",
    type=["jpg", "jpeg", "png"]
)

if uploaded:

    image = Image.open(uploaded)

    st.image(image, width=450)

    buffered = BytesIO()
    image.save(buffered, format="PNG")

    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    if st.button("AI 설명 생성"):

        with st.spinner("이미지를 분석하는 중..."):

            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text":
"""
당신은 시각장애인을 위한 안내 도우미입니다.

다음 형식으로 설명하세요.

## 전체 상황

## 중요한 위험 요소

## 사용자가 해야 할 행동

## 3줄 요약

쉬운 단어를 사용하세요.
"""
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{img_base64}"
                            }
                        ]
                    }
                ]
            )

        answer = response.output_text

        st.success("분석 완료")

        st.markdown(answer)

        st.session_state["answer"] = answer


if "answer" in st.session_state:

    st.divider()

    st.subheader("이미지에 대해 질문하기")

    question = st.text_input("질문을 입력하세요")

    if st.button("질문하기"):

        response = client.responses.create(
            model="gpt-4.1",
            input=f"""
이미지 설명

{st.session_state['answer']}

질문

{question}
"""
        )

        st.write(response.output_text)
