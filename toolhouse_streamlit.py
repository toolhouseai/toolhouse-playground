import streamlit as st
from typing import List
from toolhouse import Toolhouse
from llms import llms, llm_call
import dotenv
import json

dotenv.load_dotenv()

st.title("💬 Toolhouse demo")
st.logo(
    "logo.svg",
    link="https://toolhouse.ai")

with st.sidebar:
    llm_choice = st.selectbox("Model", tuple(llms.keys()))
    user = st.text_input("User")

llm = llms.get(llm_choice)
provider = llm.get('provider')
model = llm.get('model')

th = Toolhouse(provider=llm.get('provider'))
th.set_metadata('id', 'daniele')

if "messages" not in st.session_state:
    st.session_state.messages = []

def format_messages():
    # return [{ "role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    return st.session_state.messages

def append_and_print(response):
    with st.chat_message("assistant"):
        if provider == 'anthropic':
            if response.content is not None:
                st.session_state.messages.append({"role": "assistant", "content": response.content})
                text = next((c.text for c in response.content if hasattr(c, "text")), '…')
                st.write(text)
        else:
            st.session_state.messages.append(response.choices[0].message.model_dump())
            if (text := response.choices[0].message.content) is not None:
                st.write(text)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if provider == 'anthropic':
            text = next(c.text for c in message["content"] if hasattr(c, "text")) if message["role"] == "assistant" else message["content"]
            st.markdown(text)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = llm_call(
        provider=llm_choice,
        model=model,
        messages=format_messages(),
        stream=False,
        tools=th.get_tools(),
        max_tokens=4096,
    )

    append_and_print(response)
    print(json.dumps(st.session_state.messages, indent=4))
    tool_results = th.run_tools(response)

    if tool_results:
        st.session_state.messages += tool_results
        after_tool_response = llm_call(
            provider=llm_choice,
            model=model,
            messages=format_messages(),
            stream=False,
            tools=th.get_tools(),
            max_tokens=4096,
        )
        append_and_print(after_tool_response)
