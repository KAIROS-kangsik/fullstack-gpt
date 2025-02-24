# 이 코드는 Streamlit을 사용하여 웹사이트의 내용을 로드하고,
# 그 내용을 텍스트로 변환하여 표시하는 애플리케이션을 만듭니다.
# 주요 목적은 AsyncChromiumLoader를 사용하여 비동기적으로 웹페이지를 로드하고,
# Html2TextTransformer를 사용하여 HTML을 텍스트로 변환하는 과정을 구현하는 것입니다.
#
# 이번 시간에 공부할 내용:
# - AsyncChromiumLoader를 이용해서 웹사이트에서 정보를 비동기적으로 가져오는 방법
# - Langchain 라이브러리의 도구를 활용한 웹 스크래핑과 데이터 처리 기초


from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import (
    Html2TextTransformer,
)  # document를 transform(변형)시켜준다. format(형식)을 바꿔주는 것이다.
import streamlit as st

st.set_page_config(
    page_icon="🤖",
    page_title="SiteGPT",
)

# Html2TextTransformer: HTML 콘텐츠를 텍스트로 변환하는 도구
# - Langchain에서 제공하는 변환기 클래스
# - HTML 태그를 제거하고, 사람이 읽기 쉬운 텍스트만 추출
# - 입력: Document 객체 리스트, 출력: 변환된 Document 객체 리스트
html2text_transformer = Html2TextTransformer()

st.markdown(
    """
    # SiteGPT
            
    웹사이트의 내용에 대해 질문하세요.

    사이드바에 URL을 입력하고 시작하세요.
"""
)

with st.sidebar:
    url = st.text_input(
        "URL을 입력하세요.",
        placeholder="https://example.com",
    )

if url:
    loader = AsyncChromiumLoader([url])
    # AsyncChromiumLoader: Langchain에서 제공하는 비동기 웹페이지 로더
    # - Playwright를 기반으로 Chromium 브라우저를 헤드리스(화면 없이) 실행
    # - 자바스크립트가 실행된 후의 최종 HTML을 가져옴
    # - 역할: 주어진 URL 리스트를 받아 Chromium 브라우저를 준비
    # - 특징: 비동기 방식으로 여러 페이지를 동시에 로드 가능 (효율적)
    # 주의: Streamlit은 동기 환경이므로, 비동기 메서드(aload)를 사용할 때는
    #       asyncio.run()이나 nest_asyncio를 활용해야 함

    # 비동기 방식 설명
    # - 동기: 페이지1 로드 → 완료 대기 → 페이지2 로드 (순차적, 느림)
    # - 비동기: 페이지1 로드 시작 → 대기 없이 페이지2 로드 시작 → 완료 시 결과 수집 (빠름)

    # docs = loader.load()  # 현재 코드에서는 load() 사용 중
    # 주의: AsyncChromiumLoader는 비동기 클래스인데, load()는 동기 메서드임
    #       제대로 비동기 처리를 하려면 아래와 같이 수정 필요:
    # import asyncio
    # docs = asyncio.run(loader.aload())  # aload()가 비동기 로드 메서드
    # 또는 nest_asyncio 적용 후 사용:
    # import nest_asyncio
    # nest_asyncio.apply()
    # docs = loader.load()

    docs = loader.load()  # 임시로 load() 사용, 나중에 비동기 처리로 변경 권장
    # load() 메서드 (또는 aload())
    # - 입력: 없음 (URL은 AsyncChromiumLoader 생성 시 이미 전달됨)
    # - 출력: Document 객체 리스트
    #   - Document: Langchain에서 사용하는 데이터 구조
    #     - page_content: 웹페이지의 HTML 콘텐츠 (문자열)
    #     - metadata: URL 등의 추가 정보 (딕셔너리)
    #   - 예: [Document(page_content="<html>...</html>", metadata={"source": "url"})]
    # - 용도: 이후 텍스트 변환, 질문 처리 등에 활용

    # HTML을 텍스트로 변환
    transformed = html2text_transformer.transform_documents(docs)
    # transform_documents()
    # - 입력: Document 객체 리스트 (HTML 콘텐츠 포함)
    # - 출력: HTML이 텍스트로 변환된 Document 객체 리스트
    # - 동작: HTML 태그 제거, 텍스트 콘텐츠만 남김
    st.write(transformed)
