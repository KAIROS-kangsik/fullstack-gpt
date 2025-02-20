# streamlit에서 데이터가 바뀌면 코드의 처음부터 끝까지 전체가 재실행 된다.


import streamlit as st
from datetime import datetime

today = datetime.today().strftime("%H:%M:%S")

st.title(today)

st.selectbox("Choose your model", ("GPT-3.5", "GPT-4"))
