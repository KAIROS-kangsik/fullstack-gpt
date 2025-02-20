from typing import Dict, List
from uuid import UUID
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st

st.set_page_config(
    page_icon="🤖",
    page_title="DocumentGPT",
)


class ChatCallbackHandler(BaseCallbackHandler):

    message = ""

    def on_llm_start(self, *args, **kwargs):
        self.message_box = st.empty()

    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")

    def on_llm_new_token(self, token, *args, **kwargs):
        self.message += token
        self.message_box.markdown(self.message)


llm = ChatOpenAI(
    temperature=0.1,
    streaming=True,
    callbacks=[
        ChatCallbackHandler(),
    ],
)


@st.cache_resource(show_spinner="Embedding file...")
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    embeddings = OpenAIEmbeddings()
    cache_dir = LocalFileStore(f"./.cache/embeddings/{file.name}")
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        embeddings,
        cache_dir,
    )
    vectorstore = Chroma.from_documents(docs, cached_embeddings)
    retriever = vectorstore.as_retriever()
    return retriever
    # @st.cache_resource라는 데코레이터를 통해서, Streamlit은 여기에 어떤 파일이 있는지 확인부터 할것이다.
    # 그리고 파일이 동일하다면, Streamlit은 이 함수를 재실행시키지 않을 것이다.
    # 다시 말해서 이 embed_file이라는 함수는 처음에는 실행 될 것이다.
    # 두번째에는 파일이 변하지 않았을 때, 즉 유저가 다른 파일을 올리지 않았을 때 함수가 재실행되는 대신에,
    # Streamlit은 함수 실행을 건너 뛸 것이고, 그리고 이 함수를 실행하는 대신에 기존에 반환했던 값을 다시 반환할 것이다.


def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})


def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)


def paint_history():
    for message in st.session_state["messages"]:
        send_message(message["message"], message["role"], save=False)


def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)
    # 방법 2: 일반적인 for 반복문(위의 코드와 완전 같은 코드)
    # result = []
    # for document in docs:
    #     result.append(document.page_content)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Answer the question using ONLY the following context.
            If you don't know the answer just say you don't know.
            DON'T make anything up.
            And if the user asks a question in Korean, answer in Korean, and if the user asks a question in English, answer in English.
     
            Context: {context}
            """,
        ),
        ("human", "{question}"),
    ]
)

st.title("DocumentGPT")

st.markdown(
    """
    안녕하세요!

    챗봇을 사용하여 파일에 대해 인공지능에게 질문하세요.

    파일을 사이드바에 업로드해 주세요.
    """
)

with st.sidebar:
    file = st.file_uploader(
        "txt, pdf, docx 파일을 업로드 하세요.",
        type=["pdf", "txt", "docx"],
    )

if file:
    retriever = embed_file(file)
    send_message("파일을 모두 읽었습니다. 무엇을 도와드릴까요?", "ai", save=False)
    paint_history()
    message = st.chat_input("파일에 대해 무엇이든지 물어보세요.")
    if message:
        send_message(message, "human")
        chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
        )
        with st.chat_message("ai"):
            chain.invoke(message)
else:
    st.session_state["messages"] = []
