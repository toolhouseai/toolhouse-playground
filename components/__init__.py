import streamlit as st
import requests
import pyperclip
from tools import tool_prompts, generate_prompt_suggestions
from api.history import get_all_chats
from st_utils.url import build_url
import os

tool_req = requests.get("https://api.toolhouse.ai/me/tools")
tool_list = tool_req.json()
base_url = os.environ.get("PLAYGROUND_BASE_URL")


@st.dialog("Share this chat")
def share_dialog():
    st.markdown("You can share this chat with others by sending them this link.")
    st.markdown(
        "**Important:** People can see the entire chat history, but they won't be able to use your execution credits."
    )
    url = build_url(st.session_state.chat_id)
    left, right = st.columns([5, 1], vertical_alignment="center")
    with left:
        st.html(f'<pre class="th-share-url">{url}</pre>')
    with right:
        if st.button(
            "",
            type="tertiary",
            icon=":material/content_copy:",
            use_container_width=True,
        ):
            pyperclip.copy(url)
            st.toast("Link copied to clipboard")


def get_tool(tool_id: str):
    return next((obj for obj in tool_list if obj.get("id") == tool_id), None)


def sidebar(token):
    with st.sidebar:
        st.title(":material/chat: Playground")
        left, right = st.columns(2)
        left.link_button(
            "",
            url=f"/",
            icon=":material/library_add:",
            help="New chat",
            use_container_width=True,
        )

        disabled = "chat_id" not in st.session_state or st.session_state.chat_id is None
        if right.button(
            "",
            icon=":material/ios_share:",
            help="Share this chat",
            disabled=disabled,
            use_container_width=True,
        ):
            share_dialog()
        st.markdown(
            """
        ✨ [Join our Discord Community](https://discord.toolhouse.ai)
        """
        )
        if chat_list := get_all_chats(token):
            st.markdown("### Your chats")
            for chat in chat_list:
                active = (
                    "th-active" if chat.get("id") == st.session_state.chat_id else ""
                )
                url = build_url(chat.get("id"))
                st.html(
                    f'<a href="{url}" class="th-page-link {active}" target="_self">{chat.get("title")}'
                )


@st.dialog("You ran out of execs", width="large")
def top_up():
    url = "https://app.toolhouse.ai/billing"
    st.write("You ran out of Toolhouse execs!")
    st.write(f"You can top up your balance in the [Billing page]({url}).")
    st.link_button("Top up your balance", url, type="primary")


def hide_hero_and_call(prompt):
    st.session_state.hide_hero = True
    st.session_state.prompt = prompt


def get_suggestions():
    st.session_state.suggestion_generation_in_progress = True


def hero():
    if st.session_state.hide_hero:
        return

    tool_id = st.query_params.get("tool_id")
    tool = tool_prompts.get(tool_id)

    if not st.query_params.get("tool_id"):
        with st.chat_message("", avatar="sparkles.svg"):
            st.markdown(
                '<h2 style="padding:0;padding-bottom:1rem">Welcome to the Playground!</h2>',
                unsafe_allow_html=True,
            )
            st.write(
                "This is an interactive environment where you can test Toolhouse with the Tools you installed."
                "  \n"
                "You can use the Playground to test out a tool, or to see how multiple tools work together."
            )

            st.button(
                "I'm feeling lucky",
                on_click=get_suggestions,
                icon=":material/ifl:",
                disabled=(
                    st.session_state.suggestions is not None
                    or st.session_state.suggestion_generation_in_progress is True
                ),
            )

            if st.session_state.suggestion_generation_in_progress is True:
                with st.spinner("Generating suggestions based on your tools…"):
                    st.session_state.suggestions = generate_prompt_suggestions(
                        st.session_state.available_tools
                    )
                    st.session_state.suggestion_generation_in_progress = False

                for i, suggestion in enumerate(st.session_state["suggestions"]):
                    st.markdown(f"*{suggestion}*")
                    st.button(
                        "Try this prompt",
                        key=f"button-{i}",
                        on_click=hide_hero_and_call,
                        args=[suggestion],
                    )
    else:
        if not tool:
            st.markdown(
                f"The Playground cannot load the requested tool: `{st.query_params.get("tool_id")}`. Ensure the name is correct."
            )
            st.markdown(
                "You can try a different Tool by going to [Tool Store](https://app.toolhouse.ai/store)."
            )
            st.stop()
        elif not any(
            item["name"] == tool_id for item in st.session_state.available_tools
        ):
            st.markdown(f"## {tool.get("title")} is not installed")
            st.write(
                f"You need to install {tool.get("title")} from the Tool Store before you can use it in the Playground."
            )
            st.link_button(
                f"Go to the Tool Store",
                f"https://app.toolhouse.ai/store/{tool_id}",
                type="primary",
            )
            st.stop()
        else:
            st.markdown(
                f'<div style="display:flex;"><div><img style="width:3rem;height: 3rem;margin: 1rem 2rem" src="{tool.get("logo")}" /></div><div style="flex:1"><h2 style="font-weight:700;padding: 1rem 0">Try {tool.get('title')}</h2></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                "Click the Try button to run this tool with the following prompt and see the result."
            )
            st.markdown(f"*{tool.get("prompt")}*")
            if not st.session_state.hide_hero:
                st.button(
                    "Try this prompt",
                    key=f"button-{st.query_params.get("tool_id")}",
                    type="primary",
                    on_click=hide_hero_and_call,
                    args=[tool.get("prompt")],
                )
