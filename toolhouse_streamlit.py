import streamlit as st
from toolhouse import Toolhouse
from llms import llms, llm_call, prepare_system_prompt
from http_exceptions.client_exceptions import NotFoundException

# Check for Toolhouse API key
if not st.query_params.get("th_token"):
    st.error("Toolhouse API Key is missing!")
    st.markdown("To access the playground, you need to provide a Toolhouse API Key.")
    st.markdown("Get your API Key from the [Toolhouse dashboard](https://app.toolhouse.ai/settings/api-keys)")
    st.stop()

st.set_page_config(
    page_title="Toolhouse Playground",
    page_icon="https://app.toolhouse.ai/icons/favicon.ico",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = ""

if "stream" not in st.session_state:
    st.session_state.stream = True

if "provider" not in st.session_state:
    st.session_state.provider = llms.get(next(iter(llms))).get("provider")

from st_utils import print_messages, append_and_print
import dotenv

dotenv.load_dotenv()

st.logo("logo.svg", link="https://toolhouse.ai")

# Set some default values
llm_choice = "Llama 3.1 8B (GroqCloud)"
user= "anonymous"
bundle="default"

with st.sidebar:
    st.title("💬 Playground")
    st.markdown("""
    **Want to earn more credits?**

    
    ✨ [Join our Discord](https://discord.toolhouse.ai) and become a Toolhouse Partner
    """)

    t = Toolhouse(access_token=st.query_params["th_token"], provider="anthropic")
        
    try:
        available_tools = t.get_tools()
    except NotFoundException:
        available_tools = None

    if not available_tools:
        st.subheader("No tools installed")
        st.caption(
            "Go to the [Tool Store](https://app.toolhouse.ai/store) to install your tools, or visit [Bundles](https://app.toolhouse.ai/bundles) to check if the selected bundle exists."
        )
    else:
        st.subheader("Installed tools")
        for tool in available_tools:
            tool_name = tool.get("name")
            st.page_link(f"https://app.toolhouse.ai/store/{tool_name}", label=tool_name)

        st.caption(
            "\n\nManage your tools in the [Tool Store](https://app.toolhouse.ai/store) or your [Bundles](https://app.toolhouse.ai/bundles)."
        )

llm = llms.get(llm_choice)
st.session_state.provider = llm.get("provider")
model = llm.get("model")

try:
    th = Toolhouse(access_token=st.query_params["th_token"], provider=llm.get("provider"))
    timezone = st.query_params["tz"] or 0

    th.set_metadata("id", st.query_params["th_token"])
    th.set_metadata("timezone", timezone)
except Exception as e:
    st.error(f"Invalid API key: {str(e)}")
    st.stop()

print_messages(st.session_state.messages, st.session_state.provider)

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with llm_call(
        provider=llm_choice,
        model=model,
        messages=st.session_state.messages,
        stream=st.session_state.stream,
        tools=th.get_tools(bundle=bundle),
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
                tools=th.get_tools(bundle=bundle),
                max_tokens=4096,
                temperature=0.1,
            ) as after_tool_response:
                after_tool_response = append_and_print(after_tool_response)
                tool_results = th.run_tools(
                    after_tool_response, append=False
                )
