import json
from langchain.chat_models import ChatOpenAI
from langchain.retrievers import WikipediaRetriever
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.schema import BaseOutputParser
import streamlit as st


class JsonOutputParser(BaseOutputParser):

    def parse(self, text):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        return json.loads(text)


output_parser = JsonOutputParser()


st.set_page_config(
    page_icon="🧐",
    page_title="QuizGPT",
)

st.title("QuizGPT")

llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-3.5-turbo-1106",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
)


def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)


questions_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
    You are a helpful assistant that is role playing as a teacher.
         
    Create 10 questions in KOREAN to test your knowledge of the text based ONLY on the following context.

    Each question should have 4 answers, three of them must be incorrect and one should be correct.

    Use (o) to signal the correct answer.

    Question examples:

    Question: 바다의 색은 무슨색인가요?
    Answers: 빨강|노랑|초록|파랑(o)

    Question: 한국의 수도는 어디인가요?
    Answer: 도쿄|서울(o)|오타와|워싱턴

    Question: 아바타 영화는 언제 개봉했나요?
    Answer: 2007|2001|2009(o)|1998

    Question: 'Julius Caesar'가 누구인가요?
    Answer: 로마 황제(o)|화가|배우|모델

    Your turn!

    Context: {context}
""",
        ),
    ]
)


questions_chain = {"context": format_docs} | questions_prompt | llm

formatting_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
        You are a powerful formatting algorithm.
         
        You format exam questions into JSON format.
        Answers with (o) are the correct ones.

        Example Input:

        Question: 바다의 색은 무슨색인가요?
        Answers: 빨강|노랑|초록|파랑(o)

        Question: 한국의 수도는 어디인가요?
        Answer: 도쿄|서울(o)|오타와|워싱턴

        Question: 아바타 영화는 언제 개봉했나요?
        Answer: 2007|2001|2009(o)|1998

        Question: 'Julius Caesar'가 누구인가요?
        Answer: 로마 황제(o)|화가|배우|모델
         
         Example Output:
    ```json
    {{ "questions": [
            {{
                "question": "바다의 색은 무슨색인가요?",
                "answers": [
                        {{
                            "answer": "빨강",
                            "correct": false
                        }},
                        {{
                            "answer": "노랑",
                            "correct": false
                        }},
                        {{
                            "answer": "초록",
                            "correct": false
                        }},
                        {{
                            "answer": "파랑",
                            "correct": true
                        }},
                ]
            }},
                        {{
                "question": "한국의 수도는 어디인가요?",
                "answers": [
                        {{
                            "answer": "도쿄",
                            "correct": false
                        }},
                        {{
                            "answer": "서울",
                            "correct": true
                        }},
                        {{
                            "answer": "오타와",
                            "correct": false
                        }},
                        {{
                            "answer": "워싱턴",
                            "correct": false
                        }},
                ]
            }},
                        {{
                "question": "아바타 영화는 언제 개봉했나요?",
                "answers": [
                        {{
                            "answer": "2007",
                            "correct": false
                        }},
                        {{
                            "answer": "2001",
                            "correct": false
                        }},
                        {{
                            "answer": "2009",
                            "correct": true
                        }},
                        {{
                            "answer": "1998",
                            "correct": false
                        }},
                ]
            }},
            {{
                "question": "'Julius Caesar'가 누구인가요?",
                "answers": [
                        {{
                            "answer": "로마 황제",
                            "correct": true
                        }},
                        {{
                            "answer": "화가",
                            "correct": false
                        }},
                        {{
                            "answer": "배우",
                            "correct": false
                        }},
                        {{
                            "answer": "모델",
                            "correct": false
                        }},
                ]
            }}
        ]
     }}
    ```
    Your turn!

    Questions: {context}
""",
        ),
    ]
)

formatting_chain = formatting_prompt | llm


@st.cache_resource(show_spinner="Reading file...")
def split_file(file):
    file_content = file.read()
    file_path = f"./.cache/quiz_files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    return docs


@st.cache_resource(show_spinner="퀴즈 생성중...")
def run_quiz_chain(_docs, topic):
    chain = {"context": questions_chain} | formatting_chain | output_parser
    return chain.invoke(_docs)
    # '_docs'에 언더스코어를 붙인 이유:
    #  - 함수가 호출되어서 실행되면 파라미터가 hash된다.
    #  - 여기서 hash한다는 것은, 들어오는 데이터의 '서명'을 생성한다는 것을 의미한다.
    #  - 그래서 다시 이 함수를 호출하게 된다면 데이터의 '서명'은 변경되지 않는다.
    #  - 그러면 streamlit이 이 함수가 실행되면 안 된다는 것을 알아차리게 된다.
    #  - 그래서 이전의 값을 리턴하게 된다.
    #  - 예: "안녕하세요" -> "a123b456" (이런 식으로 서명함)
    #  - 다시 정리하면, 코드가 실행될때 컴퓨터는 "cache_resource"라는 코드가 보이면 그 밑에있는 함수를 살펴본다.
    #  - 그러면서 그 함수의 파라미터에 hash를 하여 서명을 만들어낸다.
    #  - 그래서 처음 실행되면 이 코드가 실행된다.
    #  - 하지만 두 번째로 실행될 때는 데이터의 '서명'이 같기 때문에 streamlit은 이 함수를 다시 실행시키면 안된다는 것을 알고
    #  - 대신 처음 실행에서 얻은 이전 데이터의 값을 리턴해 주는것이다.
    #
    #  - 그런데 여기서 문제는, streamlit이 docs의 파라미터의 서명을 만들어 내려고 한다는것이다. 불가능한데도 말이다.
    #  - 그래서 에러가 나는 것이다. 에러는 streamlit이 문서의 데이터 서명을 만들어내지 않도록 해야한다는 것을 알려주고 있다.
    #  - 그래서 언더스크롤을 써서 "_docs"이런식으로 매개변수의 이름을 바꿔줘야 한다.
    #  - 이건 파이썬의 문제가 아니라 streamlit의 문제이다.
    #  - streamlit은 이 _ 문자를 보고 '좋아, 데이터의 서명을 만들면 안돼'라고 생각한다.
    #  - 또 여기서 문제가 있는데 이제 _ 표시를 했으니 파라미터의 값이 변경되는 것은 아무 상관이 없게 된다.
    #  - 무슨 말이냐면, 파라미터의 값이 변경된다 하더라도 함수의 아웃풋은 항상 첫 번째것이 리턴될 것이고,
    #  - 그것이 유일하게 실행된다는 말이다.
    #  - 즉, 이 함수는 파라미터(docs)가 변경되더라도 한 번만 실행 된다.
    #  - 따라서 우리가 해야 할 일은 여기에 또 다른 매개변수를 추가하는 것이다.(여기서는 topic이라는 변수 추가함)
    #  - 그래서 다른 매개변수가 변경되면 모든 함수는 하시 실행되도록 하는 원리인 것이다.
    #  - 이건 그냥 작은 팁간은 것이다.
    #  - 해시할 수 없는 매개변수가 있거나, streamlit이 데이터의 서명을 만들 수 없는 경우
    #  - 다른 매개변수를 넣어서 이 변수가 변경되면 streamlit이 함수를 재실행 시킬 수 있도록 하는 것이다.


@st.cache_resource(show_spinner="위키피디아 검색중...")
def wiki_search(topic):
    retriever = WikipediaRetriever(top_k_results=5, lang="ko")
    docs = retriever.get_relevant_documents(topic)
    return docs


with st.sidebar:
    docs = None
    choice = st.selectbox(
        "무엇을 사용할지 선택하세요.",
        (
            "파일",
            "위키피디아",
        ),
    )
    if choice == "파일":
        file = st.file_uploader(
            "TXT, PDF, DOCX파일을 업로드 하세요.", type=["txt", "pdf", "docx"]
        )
        if file:
            docs = split_file(file)
            # st.write(docs)
    else:
        topic = st.text_input("위키피디아에서 찾을 주제를 입력하세요.")
        if topic:
            docs = wiki_search(topic)
            # st.write(docs)

if not docs:
    st.markdown(
        """
    QuizGPT에 오신것을 환영합니다!

    여러분이 요청한 위키피디아 기사나 업로드한 파일로 퀴즈를 만들어 지식을 테스트하고 공부하는 데 도움을 드립니다.

    사이드바에서 파일을 업로드하거나 위키백과에서 검색하여 시작하세요.
    """
    )
else:
    response = run_quiz_chain(docs, topic if topic else file.name)
    # topic이 있으면 topic을, 없으면 file.name을 사용
    # 삼항 연산자와 같은 역할: (topic ? topic : file.name)
    with st.form("questions form"):
        st.session_state["count"] = 0
        for question in response["questions"]:
            # st.write(question["question"])
            value = st.radio(
                question["question"],
                [answer["answer"] for answer in question["answers"]],
                index=None,  # 디폴트로 맨 처음 선택지가 이미 선택되어 있는 현상을 없애줌
            )
            if value:
                if {"answer": value, "correct": True} in question["answers"]:
                    st.session_state["count"] += 1
                    st.success("정답입니다!")
                else:
                    st.error("틀렸습니다.")
        # 내가 짠 코드
        #     for answer in question["answers"]:
        #         if value == answer["answer"] and answer["correct"] == True:
        #             st.success("정답입니다!")
        #             st.session_state["count"] += 1
        #         if value == answer["answer"] and answer["correct"] == False:
        #             st.error("틀렸습니다. 다시 푸세요")
        button = st.form_submit_button("제출")
    st.write(f'점수: {st.session_state["count"]}/{len(response["questions"])}')

# <function calliing> - gpt3, gpt4만의 특징 오직 이 두 모델에서만 사용 가능
#   이 기능으로 우리가 할 수 있는것은 두가지다
#   첫번째는 모델이 우리의 코드를 호출하도록 할 수 있고,
#   아니면 모델이 우리가 원하느 ㄴ특정 모양과 형식의 output을 갖도록 강제할 수도 있다.
