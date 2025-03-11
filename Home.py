import streamlit as st

st.set_page_config(
    page_icon="🤖",
    page_title="FullstackGPT Home",
)

st.title("FullstackGPT Home")

st.markdown(
    """
    # 안녕하세요!

    저의 FullstackGPT 포트폴리오에 오신것을 환영합니다!

    제가 만든 앱들입니다😁:

    - [x] [DocumentGPT](/DocumentGPT)  
    - [x] [PrivateGPT](/PrivateGPT)  
    - [x] [QuizGPT](/QuizGPT)  
    - [x] [SiteGPT](/SiteGPT)  
    - [ ] [MeetingGPT](/MeetingGPT)  
    - [ ] [InvestorGPT](/InvestorGPT)  
    """
)

with st.sidebar:
    video = st.file_uploader(
        "Video",
        type=["mp4", "avi", "mkv", "mov"],
    )
