# Full Stack GPT

LangChain 연습!

Code Challenge!> PrivateGPT나 DocumentGPT의 사이드바에 드롭다운으로 파일을 올릴 수 있게 하고, 그 밑에 모델을 변결할 수 있게 만들자. 다른 모델은 로컬에서 실행되는 모델들로 채우자.

Code Challenge!> QuizGPT에서 사이드바에 스위치를 만들어서 스위치를 키면 정답을 보여주는 동작을 만들자

Code Challenge!> SiteGPT에서 ChatBot처럼 보이게 만들자. streaming, 사용자 및 assistant message, chat history...등등이 필요할 것이다. 이런 것들을 만들어서 진짜 챗봇을 구현해보자<br>
또한 사용자 question을 cache해보자. 똑같은 질문ㅇ르 받으면 LLM에게 반복적으로 질문하는 것보다, 이미 한번 얻은 답변을 반환하는게 좋을 것이다.<br>
더 개선하려면, 비슷한 question들의 cache도 도전해보자. 무슨 말이냐면, 처음 question을 받았을 때, 응답을 보내면서 그 응답을 어딘가에 저장도 해놓는 것이다. 그리고 또 그 응답(response)을 생성한 question도 어딘가에 보관하는 것이다. 그리고 그 question과 비슷한 또 다른 질문을 받았을 때, retriever와 map re-rank를 작동시키기 전에, LLM에게 먼저 물어보는 것이다. 다른 LLM에게 "이봐, 네 생각엔 이런 question을 이전에 받은적 있는것 같아? 만약 있다면, 원래 질문은 뭐였지?"하고 묻는 것이다. 만약 기존에 받았던 question이 있다면 그에 대한 답변을 반환하는 것이다.
