from langchain.document_loaders import SitemapLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import streamlit as st


st.set_page_config(
    page_icon="🤖",
    page_title="SiteGPT",
)

llm = ChatOpenAI(
    temperature=0.1,
)

answers_prompt = ChatPromptTemplate.from_template(
    """
    Using ONLY the following context answer the user's question. If you can't just say you don't know, don't make anything up.

    Then, give a score to the answer between 0 and 5. 0 being not helpful to the user and 5 being helpful to the user.

    Make sure to include the answer's score even if it's 0.

    Context: {context}

    Examples:

    Question: How far away is the moon?
    Answer: The moon is 384,400 km away.
    Score: 5

    Question: How far away is the sun?
    Answer: I don't know
    Score: 0

    Your turn!

    Question: {question}
"""
)


def get_answers(inputs):
    docs = inputs["docs"]
    question = inputs["question"]
    answers_chain = answers_prompt | llm
    # answers = []
    # for doc in docs:
    #     result = answers_chain.invoke(
    #         {
    #             "context": doc.page_content,
    #             "question": question,
    #         }
    #     )
    #     answers.append(result.content)
    # return answers
    return {
        "question": question,
        "answers": [
            {
                "answer": answers_chain.invoke(
                    {
                        "context": doc.page_content,
                        "question": question,
                    }
                ).content,
                "source": doc.metadata["source"],
                "date": doc.metadata["loc"],
            }
            for doc in docs
        ],
    }


choose_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
     Use ONLY the following pre-existing answers to answer the user's question.
     
     Use the answers that have the highest score (more helpful) and favor the most recent ones.

     Return the sources of the answers as they are, do not change them.

     Answers: {answers}
""",
        ),
        ("human", "{question}"),
    ]
)


def choose_answer(inputs):
    answers = inputs["answers"]
    question = inputs["question"]
    choose_chain = choose_prompt | llm
    # condensed = ""
    # for answer in answers:
    #     condensed += f"Answer:{answer['answer']}\nSource:{answer['source']}\nDate:{answer['date']}\n"
    # st.write(condensed)
    condensed = "\n\n".join(
        f"{answer['answer']}\nSource:{answer['source']}\nDate:{answer['date']}\n"
        for answer in answers
    )
    return choose_chain.invoke(
        {
            "answers": condensed,
            "question": question,
        }
    )


# 이 function에서 반환한 어떤 값이던 그 text는 page_content로서 document에 포함된다.
# 이게 무슨말인지 궁금하다면 return "hello"로 'hello'를 반환해보면 알게 된다.
def parse_page(soup):
    combine = ""
    title = soup.find("h3", class_="heading").get_text(strip=True)
    text = soup.find(id="article-view-content-div").get_text(strip=True)
    if text and title:
        combine = f"Title: {title}\n\nText: {text}"
    # header = soup.find("header")
    # footer = soup.find("footer")
    # if header:
    #     header.decompose() # 해당 Tag를 없애고 싶을때 사용
    # if footer:
    #     footer.decompose()
    return combine


@st.cache_resource(show_spinner="URL 읽는중...")
def load_website(url):
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000,
        chunk_overlap=200,
    )
    loader = SitemapLoader(
        url,
        filter_urls=[r"^https://www\.aitimes\.com/news/articleView\.html\?idxno=\d+$"],
        parsing_function=parse_page,
    )
    loader.requests_per_second = 1
    docs = loader.load_and_split(text_splitter=splitter)
    vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())
    # st.write(docs)
    return vector_store.as_retriever()


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
    if ".xml" not in url:
        with st.sidebar:
            st.error("Sitemap URL을 입력하세요.")
    else:
        retriever = load_website(url)
        query = st.text_input("웹사이트에 대한것을 질문하세요.")
        if query:
            chain = (
                {
                    "docs": retriever,
                    "question": RunnablePassthrough(),
                }
                | RunnableLambda(get_answers)
                | RunnableLambda(choose_answer)
            )

            result = chain.invoke(query)
            st.markdown(result.content.replace("$", "\$"))
