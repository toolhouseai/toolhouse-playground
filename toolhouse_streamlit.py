import traceback
import dotenv

dotenv.load_dotenv()

import streamlit as st
from toolhouse import Toolhouse, Provider
from datetime import datetime, timedelta
import extra_streamlit_components as stx
from http_exceptions.client_exceptions import PaymentRequiredException
from llms import llms, llm_call
from http_exceptions.client_exceptions import NotFoundException
from st_utils import print_messages, append_and_print
from components import sidebar, hero, top_up
from decrypt import decrypt
from api.history import get_chat_history, upsert_chat_history
from api.api_key import get_api_key
import os

st.set_page_config(
    page_title="Toolhouse Playground",
    page_icon="https://app.toolhouse.ai/icons/favicon.ico",
)
cookie_manager = stx.CookieManager()

if "api_key" not in st.session_state:
    st.session_state.api_key = None

if "jwt" not in st.session_state:
    st.session_state.jwt = None

try:
    if st.query_params.get("token"):
        token = st.query_params.get("token")
        jwt = decrypt(token)
        api_key = get_api_key(jwt)

        if api_key:
            session_length = datetime.now() + timedelta(days=364)
            cookie_manager.set("token", jwt, expires_at=session_length)
            st.session_state.api_key = api_key
            st.session_state.jwt = jwt
    elif cookie_manager.get("token"):
        jwt = cookie_manager.get("token")
        api_key = get_api_key(jwt)

        if api_key:
            session_length = datetime.now() + timedelta(days=364)
            cookie_manager.set("token", jwt, expires_at=session_length)
            st.session_state.api_key = api_key
            st.session_state.jwt = jwt
    else:
        raise ValueError()

    th = Toolhouse(access_token=st.session_state.api_key, provider=Provider.ANTHROPIC)
    th.set_base_url(os.environ.get("TOOLHOUSE_BASE_URL", "https://api.toolhouse.ai/v1"))
except Exception as e:
    st.error(
        "You need a valid Toolhouse API Key in order to access the Toolhouse Playground."
        "Please go back to your Toolhouse and click Playground to start a new session."
    )
    st.stop()


st.markdown(
    "<style>@import url('https://fonts.googleapis.com/css2?family=Rethink+Sans:ital,wght@0,400..800;1,400..800&display=swap');</style>",
    unsafe_allow_html=True,
)
st.markdown(
    '<style>body, div, h1, h2, h3, h4, h4, h5, button,input,optgroup,select,textarea {font-family: "Rethink Sans" !important}</style>',
    unsafe_allow_html=True,
)

# Check for Toolhouse API key
if not api_key:
    st.markdown("# Your Toolhouse API Key is missing")
    st.markdown("To use the Playground, you need to provide a Toolhouse API Key.")
    st.markdown(
        "Get your API Key from the [Toolhouse dashboard](https://app.toolhouse.ai/settings/api-keys)."
    )
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "stream" not in st.session_state:
    st.session_state.stream = True

if "provider" not in st.session_state:
    st.session_state.provider = llms.get(next(iter(llms))).get("provider")

if "prompt" not in st.session_state:
    st.session_state.prompt = None

if "available_tools" not in st.session_state:
    try:
        st.session_state.available_tools = th.get_tools()
    except NotFoundException:
        st.session_state.available_tools = None

if "hide_hero" not in st.session_state:
    st.session_state.hide_hero = False

if st.query_params.get("chat"):
    st.session_state.hide_hero = True

if "suggestions" not in st.session_state:
    st.session_state.suggestions = None

if "suggestion_generation_in_progress" not in st.session_state:
    st.session_state.suggestion_generation_in_progress = False

if "ready" not in st.session_state:
    st.session_state.ready = False

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if st.query_params.get("chat"):
    st.session_state.chat_id = st.query_params.get("chat")

st.logo("logo.svg", link="https://app.toolhouse.ai")

# Set some default values
llm_choice = "Claude 3.5 Sonnet"

llm = llms.get(llm_choice)
st.session_state.provider = llm.get("provider")
model = llm.get("model")

th.set_metadata("id", api_key)


def hide_hero():
    st.session_state.hide_hero = True


def call_llm(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with llm_call(
            provider=llm_choice,
            model=model,
            messages=st.session_state.messages,
            stream=st.session_state.stream,
            tools=st.session_state.available_tools,
            max_tokens=4096,
            temperature=0.1,
        ) as response:
            completion = append_and_print(response)
            tool_results = th.run_tools(completion, append=False)

            while tool_results:
                st.session_state.messages += tool_results
                with llm_call(
                    provider=llm_choice,
                    model=model,
                    messages=st.session_state.messages,
                    stream=st.session_state.stream,
                    tools=st.session_state.available_tools,
                    max_tokens=4096,
                    temperature=0.1,
                ) as after_tool_response:
                    after_tool_response = append_and_print(after_tool_response)
                    tool_results = th.run_tools(after_tool_response, append=False)
    except PaymentRequiredException:
        top_up()


sidebar(cookie_manager.get("token"))
hero()


if (chat_id := st.query_params.get("chat")) and st.session_state.ready == False:
    st.session_state.chat_id = chat_id
    st.session_state.ready = True
    try:
        if not (messages := get_chat_history(chat_id, cookie_manager.get("token"))):
            raise ValueError

        st.session_state.messages = messages
    except Exception as e:
        print(e)
        st.error(
            "This chat does not exist or you don't have permissions to see it.",
            icon=":material/block:",
        )

        st.link_button("Start a new chat", url=f"/?token={token}", type="primary")

        st.page_link(
            label="Back to Toolhouse",
            page=f"https://app.toolhouse.ai",
            icon=":material/arrow_back:",
        )
        st.stop()

print_messages(st.session_state.messages, st.session_state.provider)

if st.session_state.prompt is not None:
    st.session_state.hide_hero = True
    call_llm(st.session_state.prompt)
    st.session_state.prompt = None

if "api_key" not in st.session_state or st.session_state.api_key is None:
    st.markdown("#### Run this chat for free")
    st.markdown(
        "Sign up for Toolhouse and try hundreds of agentic chats like these for free."
    )
    st.link_button(
        "Sign up for free",
        url="https://app.toolhouse.ai/sign-up",
    )

else:
    if prompt := st.chat_input("What is up?", on_submit=hide_hero):
        st.session_state.prompt = prompt
        call_llm(prompt)
        st.session_state.prompt = None

        chat_id = upsert_chat_history(
            st.session_state.chat_id,
            st.session_state.messages,
            st.session_state.jwt,
        )

        if chat_id and chat_id != st.session_state.chat_id:
            st.session_state.chat_id = chat_id
            st.rerun()
