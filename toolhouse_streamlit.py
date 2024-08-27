import streamlit as st
from toolhouse import Toolhouse
from llms import llms, llm_call
import requests

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

with st.sidebar:
    st.title("💬 Playground")
    st.markdown("#### Get your $150: join.toolhouse.ai")
    image = st.image("join.png")
    with st.expander("Advanced"):
        llm_choice = st.selectbox("Model", tuple(llms.keys()))
        st.session_state.stream = st.toggle("Stream responses", True)
        user = st.text_input("User", "daniele")
        bundle = st.text_input("Bundle", "default")
    
    t = Toolhouse(provider="anthropic")
    available_tools = t.get_tools(bundle=bundle)

    if not available_tools:
        st.subheader("No tools installed")
        st.caption(
            "Go to the [Tool Store](https://app.toolhouse.ai/store) to install your tools."
        )
    else:
        st.subheader("Installed tools")
        for tool in available_tools:
            tool_name = tool.get("name")
            st.page_link(f"https://app.toolhouse.ai/store/{tool_name}", label=tool_name)

        st.caption(
            "\n\nManage your tools in the [Tool Store](https://app.toolhouse.ai/store)."
        )
    




llm = llms.get(llm_choice)
st.session_state.provider = llm.get("provider")
model = llm.get("model")

th = Toolhouse(provider=llm.get("provider"))

th.set_metadata("timezone", -7)
if user:
    th.set_metadata("id", user)

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
