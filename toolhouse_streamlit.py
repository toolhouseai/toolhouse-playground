import streamlit as st
import streamlit.components.v1 as components
from toolhouse import Toolhouse
from toolhouse.models import OpenAIStream, stream_to_chat_completion
from llms import llms, llm_call
import dotenv

dotenv.load_dotenv()

st.title("💬 Toolhouse demo")
st.logo(
    "logo.svg",
    link="https://toolhouse.ai")

base_url = 'https://66951f1e2cff11b2ba52.appwrite.global/v1'

with st.sidebar:
    llm_choice = st.selectbox("Model", tuple(llms.keys()))
    stream = st.toggle("Stream responses", True)
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

def openai_stream(response, completion):
    for chunk in response:
        yield chunk    
        completion.add(chunk)

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
                stream_completion = OpenAIStream()
                r = st.write_stream(openai_stream(response, stream_completion))
                completion = stream_to_chat_completion(stream_completion)
                if completion.choices[0].message.tool_calls:
                    st.session_state.messages.append(completion.choices[0].message.model_dump())
                else:
                    st.session_state.messages.append({"role": role, "content": r})
                return stream_completion
            else:
                st.session_state.messages.append(response.choices[0].message.model_dump())
                if (text := response.choices[0].message.content) is not None:
                    st.write(text)
                elif response.choices[0].message.tool_calls:
                    tool_calls = response.choices[0].message.tool_calls
                    tools = [t.function.name for t in tool_calls]
                    st.write(f"Calling: " + ", ".join(tools))
                return response


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
    
    completion = append_and_print(response)
    tool_results = th.run_tools(completion, stream=stream, append=False)
    
    print(st.session_state.messages, end="\n\n\n")
    print(tool_results, end="\n\n\n")
    while tool_results:
        st.session_state.messages += tool_results
        after_tool_response = llm_call(
            provider=llm_choice,
            model=model,
            messages=st.session_state.messages,
            stream=stream,
            tools=th.get_tools(),
            max_tokens=4096,
        )
        after_tool_response = append_and_print(after_tool_response)
        tool_results = th.run_tools(after_tool_response, stream=stream)