import streamlit as st
from openai import OpenAI
from typing import List
import requests
import json
import os
from toolhouse import Toolhouse

st.title("💬 LLM Email Chatbot")

#openai_api_key = os.getenv("OPENAI_API_KEY")
def print_chat(response):
    with st.chat_message("assistant"):
        if response.choices[0].message.content is not None:
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
            response = response.choices[0].message.content
            st.write(response)

openai_api_key = st.text_input("OpenAI API Key", type="password")
TH_TOKEN = st.text_input("Toolhouse API Key", type="password")
if not openai_api_key or not TH_TOKEN:
    st.info("Please add your API key(s)/info to continue.", icon="🗝️")
else:

    client = OpenAI(api_key=openai_api_key)
    th = Toolhouse(access_token=TH_TOKEN, provider="openai")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        msgs: List = [
            {"role": "system", "content": "You are a helpful assistant that can do a variety of tasks. You can send emails."}
            ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            stream=False,
            tools=th.get_tools(),
            tool_choice="auto",
        )
        print_chat(response)
        if response.choices[0].finish_reason == "tool_calls":
            if response.choices[0].message.tool_calls:
                msgs += th.run_tools(response)
                after_tool_response = client.chat.completions.create( model="gpt-4o", messages=msgs,)
                print_chat(after_tool_response)