import streamlit as st
from toolhouse import Toolhouse, Provider
from llms import llms, llm_call
from http_exceptions.client_exceptions import NotFoundException
from st_utils import print_messages, append_and_print
from tools import tool_prompts
from components import sidebar, hero
import dotenv

try:
    th = Toolhouse(access_token=st.query_params["th_token"], provider=Provider.ANTHROPIC)
except:
    st.error(
        "You need a valid Toolhouse API Key in order to access the Toolhouse Playground."
        "Please go back to your Toolhouse and click Playground to start a new session.")
    st.stop()

dotenv.load_dotenv()

st.set_page_config(
    page_title="Toolhouse Playground",
    page_icon="https://app.toolhouse.ai/icons/favicon.ico",
)

st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Rethink+Sans:ital,wght@0,400..800;1,400..800&display=swap');</style>", unsafe_allow_html=True)
st.markdown('<style>body, div, h1, h2, h3, h4, h4, h5, button,input,optgroup,select,textarea {font-family: "Rethink Sans" !important}</style>', unsafe_allow_html=True)
tool_id = st.query_params.get("tool_id")
tool = tool_prompts.get(tool_id)

# Check for Toolhouse API key
if not st.query_params.get("th_token"):
    st.markdown("# Your Toolhouse API Key is missing")
    st.markdown("To use the Playground, you need to provide a Toolhouse API Key.")
    st.markdown("Get your API Key from the [Toolhouse dashboard](https://app.toolhouse.ai/settings/api-keys).")
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
    
if "suggestions" not in st.session_state:
    st.session_state.suggestions = None

st.logo("logo.svg", link="https://app.toolhouse.ai")

# Set some default values
llm_choice = "Claude 3.5 Sonnet"

llm = llms.get(llm_choice)
st.session_state.provider = llm.get("provider")
model = llm.get("model")

timezone = st.query_params["tz"] or 0

th.set_metadata("id", st.query_params["th_token"])
th.set_metadata("timezone", timezone)
    
def hide_hero():
    st.session_state.hide_hero = True

def call_llm(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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
        tool_results = th.run_tools(
            completion, append=False
        )

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
                tool_results = th.run_tools(
                    after_tool_response, append=False
                )

sidebar()
hero()
print_messages(st.session_state.messages, st.session_state.provider)

if st.session_state.prompt is not None:
    st.session_state.hide_hero = True
    call_llm(st.session_state.prompt)
    st.session_state.prompt = None

if prompt := st.chat_input("What is up?", on_submit=hide_hero):
    st.session_state.prompt = prompt
    call_llm(prompt)
    st.session_state.prompt = None
    