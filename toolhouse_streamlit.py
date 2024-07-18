import streamlit as st
from toolhouse import Toolhouse
from llms import llms, llm_call

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = ''

if "stream" not in st.session_state:
    st.session_state.stream = True

if "provider" not in st.session_state:
    st.session_state.provider = llms.get(next(iter(llms))).get('provider')
    
from st_utils import print_messages, append_and_print
import dotenv

dotenv.load_dotenv()

st.title("💬 Toolhouse demo")
st.logo(
    "logo.svg",
    link="https://toolhouse.ai")

with st.sidebar:
    llm_choice = st.selectbox("Model", tuple(llms.keys()))
    stream = st.toggle("Stream responses", st.session_state.stream)
    user = st.text_input("User")
    st.divider()
    t = Toolhouse(provider='anthropic')
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
if user:
    th.set_metadata('id', user)

print_messages(st.session_state.messages, provider)

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with llm_call(
        provider=llm_choice,
        model=model,
        messages=st.session_state.messages,
        stream=stream,
        tools=th.get_tools(),
        max_tokens=4096,
    ) as response:    
        completion = append_and_print(response)
        tool_results = th.run_tools(completion, stream=stream, append=False)
        
        while tool_results:
            st.session_state.messages += tool_results
            with llm_call(
                provider=llm_choice,
                model=model,
                messages=st.session_state.messages,
                stream=stream,
                tools=th.get_tools(),
                max_tokens=4096,
            ) as after_tool_response:
                after_tool_response = append_and_print(after_tool_response)
                tool_results = th.run_tools(after_tool_response, stream=stream)