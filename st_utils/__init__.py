import streamlit as st
from toolhouse.models import OpenAIStream, stream_to_chat_completion
# from anthropic.types import TextBlock, ToolUseBlock
# st.session_state.messages = [{'role': 'user', 'content': 'hi!'}, {'role': 'assistant', 'content': [TextBlock(text="Hello! It's nice to meet you. How can I assist you today? Is there anything specific you'd like help with?", type='text')]}, {'role': 'user', 'content': 'can you tell the time?'}, {'role': 'assistant', 'content': [TextBlock(text='Certainly! I\'d be happy to tell you the current time. To do that, I\'ll use the "current_time" function to fetch the most up-to-date information for you.', type='text'), ToolUseBlock(id='toolu_01A7BjS3dLRP18e2cS3YKhkF', input={}, name='current_time', type='tool_use')]}, {'role': 'user', 'content': [{'tool_use_id': 'toolu_01A7BjS3dLRP18e2cS3YKhkF', 'content': '"2024-07-17T19:45:57.566838-07:00"', 'type': 'tool_result'}]}, {'role': 'assistant', 'content': [TextBlock(text="\n\nBased on the information I've received, the current time is July 17, 2024, at 7:45:57 PM Pacific Daylight Time (PDT).\n\nIs there anything else you'd like to know or any other way I can assist you?", type='text')]}, {'role': 'user', 'content': "that's all, thank you!"}, {'role': 'assistant', 'content': [TextBlock(text="You're welcome! I'm glad I could help you with the current time. If you need any further assistance in the future, whether it's checking the time again or help with any other tasks, please don't hesitate to ask. Have a great rest of your day!", type='text')]}]

def anthropic_stream(response):
    for chunk in response.text_stream:
        yield chunk

def openai_stream(response, completion):
    for chunk in response:
        yield chunk    
        completion.add(chunk)

def print_messages(messages, provider):
    for message in messages:
        if provider == "anthropic":
            if isinstance(message["content"], str):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            elif isinstance(message["content"], list):
                for m in message["content"]:
                    if not hasattr(m, "type"):
                        continue
                    elif m.type == "text":
                        with st.chat_message(message["role"]):
                            st.markdown(m.text)
                    elif m.type == "tool_use":
                        with st.chat_message("tool"):
                            st.markdown(f"`{m.name}({m.input})`")
        else:            
            if isinstance(message.get("tool_calls"), list):
                with st.chat_message("tool"):
                    print(message["tool_calls"])
                    calls = [f"`{c["function"]["name"]}({c["function"]["arguments"]})`" for c in message["tool_calls"]]
                    st.markdown('\n'.join(calls))
            elif message["role"] != "tool":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

def append_and_print(response, role = "assistant"):
    with st.chat_message(role):
        if st.session_state.provider == 'anthropic':
            if st.session_state.stream:
                r = st.write_stream(anthropic_stream(response))
                st.session_state.messages.append({ "role": role, "content": response.get_final_message().content })
                return response.get_final_message()
            else:
                if response.content is not None:
                    st.session_state.messages.append({"role": role, "content": response.content})
                    text = next((c.text for c in response.content if hasattr(c, "text")), '…')
                    st.write(text)
                return response
        else:
            if st.session_state.stream:
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
