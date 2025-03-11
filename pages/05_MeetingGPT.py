import streamlit as st
import subprocess
from pydub import AudioSegment
import math
import glob
import openai
import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import StrOutputParser
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings

st.set_page_config(
    page_icon="🤖",
    page_title="MeetingGPT",
)

llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o",
)

has_transcript = False

# os.path.exists("./.cache/podcast.txt")

client = openai.OpenAI()

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=800,
    chunk_overlap=200,
)


@st.cache_resource()
def embed_file(file_path):
    file_name = os.path.basename(file_path)
    loader = TextLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    embeddings = OpenAIEmbeddings()
    cache_dir = LocalFileStore(f"./.cache/embeddings/{file_name}")
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        embeddings,
        cache_dir,
    )
    vectorstore = FAISS.from_documents(docs, cached_embeddings)
    retriever = vectorstore.as_retriever()
    return retriever


@st.cache_resource()
def extract_audio_from_video(video_path):
    if has_transcript:
        return
    audio_path = video_path.replace("mp4", "mp3")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        audio_path,
    ]
    # 이렇게 배열로 형태로 전달하는 것은 보안때문이다. 또한 특수 문자가 포함되어 있을때도 더 편리하기 때문에
    # 배열방식이 권장된다.
    subprocess.run(command)


@st.cache_resource()
def cut_audio_in_chunks(audio_path, chunk_size, chunks_folder):
    if has_transcript:
        return
    track = AudioSegment.from_mp3(audio_path)
    chunk_len = chunk_size * 60 * 1000  # 5분을 밀리초 단위로 변환
    chunks = math.ceil(len(track) / chunk_len)  # ceil은 올림 할때 쓰는 함수

    for i in range(chunks):
        start_time = i * chunk_len
        end_time = (i + 1) * chunk_len

        if i < chunks - 1:
            splited_track = track[start_time:end_time]
            splited_track.export(f"{chunks_folder}/chunk_{i}.mp3", format="mp3")
        else:
            splited_track = track[start_time:]
            splited_track.export(f"{chunks_folder}/chunk_{i}.mp3", format="mp3")


@st.cache_resource()
def transcribe_chunks(chunk_folder, destination):
    if has_transcript:
        return
    files = glob.glob(f"{chunk_folder}/*.mp3")
    files.sort()  # glob으로 파일을 가져올때 파일을 가져오는 순서는 뒤죽박죽이다.
    # 따라서 파일을 가져와 리스트를 만들고 그 리스트를 sort로 정렬해줘야 한다.
    for file in files:
        with open(file, "rb") as audio_file, open(destination, "a") as text_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
            text_file.write(transcript.text)


st.markdown(
    """
    # MeetingGPT
            
    미팅GPT에 오신 것을 환영하며, 동영상을 업로드하면 대본과 요약, 채팅 봇을 통해 궁금한 점을 물어볼 수 있습니다.

    사이드바에서 동영상 파일을 업로드하여 시작하세요.

"""
)

with st.sidebar:
    video = st.file_uploader(
        "Video를 업로드 하세요.",
        type=["mp4", "avi", "mkv", "mov"],
    )

if video:
    chunks_folder = "./.cache/chunks"

    temp = os.path.exists(f"./.cache/{video.name.replace('mp4', 'txt')}")

    if temp:
        has_transcript = True

    with st.status("비디오 파일 읽는중...") as status:
        video_content = video.read()
        video_path = f"./.cache/{video.name}"
        transcript_path = video_path.replace("mp4", "txt")
        with open(video_path, "wb") as f:
            f.write(video_content)
        status.update(label="오디오 추출중...")
        extract_audio_from_video(video_path)
        status.update(label="오디오 파일 분할중...")
        audio_path = video_path.replace("mp4", "mp3")
        cut_audio_in_chunks(audio_path, 10, chunks_folder)
        status.update(label="오디오 파일에서 스크립트 추출중...")
        transcribe_chunks(chunks_folder, transcript_path)

    transcript_tab, summary_tab, qa_tab = st.tabs(
        [
            "스크립트",
            "요약",
            "채팅",
        ]
    )

    with transcript_tab:
        with open(transcript_path, "r") as file:
            st.write(file.read())

    with summary_tab:
        start = st.button("요약본 불러오기")

        if start:

            loader = TextLoader(transcript_path)

            docs = loader.load_and_split(text_splitter=splitter)
            first_summary_prompt = ChatPromptTemplate.from_template(
                """
                Write a concise summary of the following in Korean so that even an elementary school student can easily understand it.:
                "{text}"

                CONCISE SUMMARY
                """
            )

            first_summary_chain = first_summary_prompt | llm | StrOutputParser()

            summary = first_summary_chain.invoke({"text": docs[0].page_content})

            refine_prompt = ChatPromptTemplate.from_template(
                """
                Your job is to produce a final summary.
                We have provided an existing summary up to a certain point: {existing_summary}
                We have the opportunity to refine the existing summary (only if needed) with some more context below.
                -----------
                {context}
                -----------
                Given the new context, refine the original summary.
                If the context isn't useful, RETURN the original summary.
                If you write the refined summary, please write in Korean, making it simple enough for an elementary school student to understand easily.
                """
            )

            refine_chain = refine_prompt | llm | StrOutputParser()

            with st.status("요약 진행중...") as status:
                for i, doc in enumerate(docs[1:]):
                    status.update(label=f"문서 요약중: {i+1}/{len(docs)-1}")
                    summary = refine_chain.invoke(
                        {
                            "existing_summary": summary,
                            "context": doc.page_content,
                        }
                    )
            st.write(summary)

    with qa_tab:
        retriever = embed_file(transcript_path)

        docs = retriever.invoke("어떤 얘기를 하고 있나요? 한문장으로 말해주세요.")

        st.write(docs)
