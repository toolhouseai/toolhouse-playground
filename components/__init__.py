import streamlit as st
from tools import tool_prompts, generate_prompt_suggestions

def sidebar():
    with st.sidebar:
        st.title("💬 Playground")
        st.markdown("""
        ✨ [Join our Discord Community](https://discord.toolhouse.ai)
        """)
            
        if not st.session_state.available_tools:
            st.subheader("No tools installed")
            st.caption(
                "Go to the [Tool Store](https://app.toolhouse.ai/store) to install your tools."
            )
        else:
            st.subheader("Installed tools")
            st.caption("Click on a tool to see its details.")
            for tool in st.session_state.available_tools:
                tool_name = tool.get("name")
                st.page_link(f"https://app.toolhouse.ai/store/{tool_name}", label=tool_name)

            st.caption(
                "\n\nManage your tools in the [Tool Store](https://app.toolhouse.ai/store)."
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
    tool_id = st.query_params.get("tool_id")
    tool = tool_prompts.get(tool_id)
    
    if not st.query_params.get("tool_id"):
      with st.chat_message("user"):
        st.markdown('<h2 style="padding:0;padding-bottom:1rem">Welcome to the Playground!</h2>', unsafe_allow_html=True)
        st.write(
            "This is an interactive environment where you can test Toolhouse with the Tools you installed."
            "  \n"
            "You can use the Playground to test out a tool, or to see how multiple tools work together."
        )
        
        st.button("Try some suggestions", on_click=get_suggestions, disabled=(st.session_state.suggestions is not None or st.session_state.suggestion_generation_in_progress is True))

        if st.session_state.suggestion_generation_in_progress is True:
            with st.spinner("Generating suggestions based on your tools…"):
                st.session_state.suggestions = generate_prompt_suggestions(st.session_state.available_tools)
                st.session_state.suggestion_generation_in_progress = False
                    
            for i, suggestion in enumerate(st.session_state["suggestions"]):
                st.markdown(f"*{suggestion}*")
                st.button("Try this prompt", key=f"button-{i}", on_click=hide_hero_and_call, args=[suggestion])
    else:
        if not tool:
            st.markdown(f"The Playground cannot load the requested tool: `{st.query_params.get("tool_id")}`. Ensure the name is correct.")
            st.markdown("You can try a different Tool by going to [Tool Store](https://app.toolhouse.ai/store).")
            st.stop()
        elif not any(item['name'] == tool_id for item in st.session_state.available_tools):
            st.markdown(f"## {tool.get("title")} is not installed")
            st.write(f"You need to install {tool.get("title")} from the Tool Store before you can use it in the Playground.")
            st.link_button(f"Go to the Tool Store", f"https://app.toolhouse.ai/store/{tool_id}", type="primary")
            st.stop()
        else:
            st.markdown(f'<div style="display:flex;"><div><img style="width:3rem;height: 3rem;margin: 1rem 2rem" src="{tool.get("logo")}" /></div><div style="flex:1"><h2 style="font-weight:700;padding: 1rem 0">Try {tool.get('title')}</h2></div>', unsafe_allow_html=True)
            st.markdown("Click the Try button to run this tool with the following prompt and see the result.")
            st.markdown(f"*{tool.get("prompt")}*")
            if not st.session_state.hide_hero:
              st.button("Try this prompt", key=f"button-{st.query_params.get("tool_id")}", type="primary", on_click=hide_hero_and_call, args=[tool.get("prompt")])
    