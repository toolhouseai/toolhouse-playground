import streamlit as st
from openai import OpenAI
from anthropic import Anthropic
from groq import Groq
from typing import List
from toolhouse import Toolhouse
from llms import llms, llm_call
import requests
import json
import os
import dotenv

dotenv.load_dotenv()

st.title("💬 Toolhouse demo")
st.logo(
    "logo.svg",
    link="https://toolhouse.ai")

with st.sidebar:
    llm_choice = st.selectbox("Model", ("GPT-4o", "Claude 3.5 Sonnet", "Llama (GroqCloud)"))
    user = st.text_input("User")

def print_chat(response):
    with st.chat_message("assistant"):
        if response.choices[0].message.content is not None:
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
            response = response.choices[0].message.content
            st.write(response)

llm = llms.get(llm_choice)
provider = llm.get('provider')
model = llm.get('model')

th = Toolhouse(provider=llm.get('provider'))
th.set_metadata('id', 'daniele')

print(th.get_tools())

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    msgs: List = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    
    response = llm_call(
        provider=llm_choice,
        model=model,
        messages=msgs,
        stream=False,
        tools=th.get_tools(),
        max_tokens=4096,
        tool_choice="auto",
    )
    print(response)
    print_chat(response)
    
    tool_results = th.run_tools(response)
    print(tool_results)    
    if tool_results:
        msgs += tool_results
        after_tool_response = llm_call(
            provider=llm_choice,
            model=model,
            messages=msgs,
            stream=False,
            tools=th.get_tools(),
            max_tokens=4096,
            tool_choice="auto",
        )
        
        msgs += after_tool_response        
        print_chat(after_tool_response)
