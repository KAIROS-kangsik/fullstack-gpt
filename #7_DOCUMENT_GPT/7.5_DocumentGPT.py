import time
import streamlit as st

st.set_page_config(
    page_icon="🤖",
    page_title="DocumentGPT",
)

st.title("DocumentGPT")

if "messages" not in st.session_state:
    st.session_state["messages"] = []
# # 위 코드는 다음을 확인합니다:
# if "messages" not in st.session_state:    # messages라는 키가 session_state 딕셔너리에 없다면
#     st.session_state["messages"] = []     # messages 키에 빈 리스트를 할당합니다

# # 위 코드는 아래 일반 딕셔너리 사용과 비슷합니다
# my_dict = {}
# if "messages" not in my_dict:
#     my_dict["messages"] = []


def send_message(message, role, save=True):
    with st.chat_message(role):
        st.write(message)
    if save:
        st.session_state["messages"].append({"message": message, "role": role})


for message in st.session_state["messages"]:
    send_message(message["message"], message["role"], save=False)


# 또는 이렇게 우리가 만든 함수를 사용하지 말고, 직접 구현해도 됨 작성해도 됨
# for obj in st.session_state["messages"]:
#     with st.chat_message(obj["role"]):
#         st.write(obj["message"])


message = st.chat_input("Send a message to the ai")

if message:
    send_message(message, "human")
    time.sleep(2)
    send_message(f"You said:{message}", "ai")
