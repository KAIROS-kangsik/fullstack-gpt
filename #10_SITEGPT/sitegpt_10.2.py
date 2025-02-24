# 이 코드는 Streamlit을 활용하여 웹사이트의 Sitemap을 로드하고,
# 그 내용을 화면에 표시하는 간단한 애플리케이션을 구현합니다.
# 주요 목적은 SitemapLoader를 사용해 Sitemap에 나열된 웹페이지 데이터를 가져오고,
# 이를 사용자에게 보여주는 과정을 실습하는 것입니다.
#
# 이번 시간에 공부한 내용:
# - SitemapLoader를 활용하여 웹사이트의 Sitemap에서 페이지 데이터를 로드하는 방법
# - Langchain 라이브러리의 기본 도구를 사용해 웹 데이터를 수집하는 기초

from langchain.document_loaders import SitemapLoader  # SitemapLoader를 가져옴
import streamlit as st  # Streamlit 라이브러리를 가져와 웹 UI 제작

# Streamlit 페이지의 기본 설정
# - page_icon: 브라우저 탭에 표시될 아이콘 설정
# - page_title: 브라우저 탭에 표시될 제목 설정
st.set_page_config(
    page_icon="🤖",  # 로봇 이모지로 페이지 아이콘 설정
    page_title="SiteGPT",  # 페이지 제목을 "SiteGPT"로 설정
)


# 웹사이트의 Sitemap을 로드하는 함수 정의
# - 역할: 주어진 Sitemap URL을 통해 웹페이지 데이터를 가져오는 기능 수행
# - 입력: url (문자열) - Sitemap의 URL
# - 출력: 로드된 문서 리스트 (docs)
@st.cache_resource(show_spinner="URL 읽는중...")
def load_website(url):
    # SitemapLoader 초기화
    # - Langchain에서 제공하는 도구로, Sitemap URL을 파싱해 나열된 페이지 콘텐츠를 로드
    # - 동작: Sitemap XML 파일을 읽고, 각 URL의 콘텐츠를 비동기적으로 가져옴
    loader = SitemapLoader(url)

    # requests_per_second 설정
    # - 초당 요청 수를 제한하여 서버에 부담을 줄이지 않도록 설정
    # - 값 1: 초당 1개의 요청만 허용 (웹사이트 예의를 지키기 위함)
    loader.requests_per_second = 1

    # load() 메서드 호출
    # - 역할: Sitemap에 나열된 모든 페이지의 콘텐츠를 로드
    # - 출력: Document 객체 리스트
    #   - Document 객체 구조:
    #     - page_content: 웹페이지의 HTML 콘텐츠 (문자열)
    #     - metadata: URL, 기타 정보를 포함한 딕셔너리
    #   - 예시: [Document(page_content="<html>...</html>", metadata={"source": "url1"}), ...]
    docs = loader.load()

    # 로드된 문서 리스트를 Streamlit 화면에 출력
    # - st.write(): Streamlit에서 데이터를 화면에 표시하는 기본 메서드
    st.write(docs)

    # 함수 호출 결과를 반환 (나중에 활용 가능하도록)
    return docs


# Streamlit 화면에 표시할 마크다운 텍스트
# - st.markdown(): 마크다운 형식의 텍스트를 화면에 렌더링
# - 내용: 애플리케이션 제목과 간단한 사용 설명
st.markdown(
    """
    # SiteGPT
            
    웹사이트의 내용에 대해 질문하세요.

    사이드바에 URL을 입력하고 시작하세요.
    """
)

# 사이드바에 URL 입력 필드 추가
# - with st.sidebar: 사이드바 영역을 정의
# - st.text_input(): 사용자가 텍스트를 입력할 수 있는 입력창 생성
with st.sidebar:
    url = st.text_input(
        "URL을 입력하세요.",  # 입력창 라벨
        placeholder="https://example.com",  # 입력창에 표시될 placeholder 텍스트
    )

# URL이 입력되었는지 확인하고 처리
# - if url: 사용자가 URL을 입력하면 아래 로직 실행
if url:
    # 입력된 URL이 Sitemap인지 확인 (".xml" 포함 여부)
    if ".xml" not in url:
        # ".xml"이 없으면 오류 메시지 출력
        # - with st.sidebar: 오류 메시지를 사이드바에 표시
        # - st.error(): 빨간색 박스에 경고 메시지 출력
        with st.sidebar:
            st.error("Sitemap URL을 입력하세요.")
    else:
        # ".xml"이 포함된 유효한 Sitemap URL이면 로드 함수 호출
        # - load_website(url): Sitemap 데이터를 로드하고 화면에 출력
        docs = load_website(url)

# 전체 코드 실행 흐름 요약:
# 1. Streamlit 페이지 설정 (아이콘, 제목 등)
# 2. 사용자가 사이드바에 Sitemap URL 입력
# 3. URL이 입력되면 ".xml" 포함 여부로 Sitemap인지 확인
# 4. 유효하지 않으면 오류 메시지 표시, 유효하면 SitemapLoader로 데이터 로드
# 5. 로드된 데이터를 화면에 출력
# 주의: Sitemap URL이 아닌 일반 URL을 입력하면 오류 메시지가 표시됨
