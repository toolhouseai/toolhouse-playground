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
    # stream = st.toggle("Stream responses", False, disabled=True)
    stream = False
    user = st.text_input("User", 'daniele')
    st.divider()
    t = Toolhouse(provider='anthropic')
    t.set_metadata('timezone', 0)
    t.set_metadata('id', 'any')
    available_tools = t.get_tools()

    if not available_tools:
        st.markdown('### No tools installed.')
    
    else:
        markdown = ['### Installed tools', '']
        for tool in available_tools:
            markdown.append(' - ' + tool.get('name'))
        
        st.markdown('\n'.join(markdown))
    

llm = llms.get(llm_choice)
provider = llm.get('provider')
model = llm.get('model')

th = Toolhouse(provider=llm.get('provider'))
th.set_metadata('timezone', -7)
th.set_metadata('id', 'daniele')

if "messages" not in st.session_state:
    st.session_state.messages = []

def anthropic_stream(response):
    for chunk in response:
        if chunk.type == 'content_block_delta':
            yield chunk.delta.text

def append_and_print(response, role = "assistant"):
    with st.chat_message(role):
        if provider == 'anthropic':
            if stream:
                r = st.write_stream(anthropic_stream(response))
                st.session_state.messages.append({ "role": role, "content": r })
                response.close()
            else:
                if response.content is not None:
                    st.session_state.messages.append({"role": role, "content": response.content})
                    text = next((c.text for c in response.content if hasattr(c, "text")), '…')
                    st.write(text)
        else:
            if stream:
                r = st.write_stream(response)
                st.session_state.messages.append({ "role": role, "content": r })
            else:
                st.session_state.messages.append(response.choices[0].message.model_dump())
                if (text := response.choices[0].message.content) is not None:
                    st.write(text)
                elif response.choices[0].message.tool_calls:
                    tool_calls = response.choices[0].message.tool_calls
                    tools = [t.function.name for t in tool_calls]
                    st.write(f"Calling: " + ", ".join(tools))


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
        messages=st.session_state.messages,
        stream=stream,
        tools=th.get_tools(),
        max_tokens=4096,
    )  
    
    append_and_print(response)
    tool_results = th.run_tools(response)
    print(tool_results)
    
    if tool_results:
        st.session_state.messages += tool_results
        after_tool_response = llm_call(
            provider=llm_choice,
            model=model,
            messages=st.session_state.messages,
            stream=stream,
            tools=th.get_tools(),
            max_tokens=4096,
        )
        append_and_print(after_tool_response)