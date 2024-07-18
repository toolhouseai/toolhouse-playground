import streamlit as st
# from anthropic.types import TextBlock, ToolUseBlock
# st.session_state.messages = [{'role': 'user', 'content': 'hi!'}, {'role': 'assistant', 'content': [TextBlock(text="Hello! It's nice to meet you. How can I assist you today? Is there anything specific you'd like help with?", type='text')]}, {'role': 'user', 'content': 'can you tell the time?'}, {'role': 'assistant', 'content': [TextBlock(text='Certainly! I\'d be happy to tell you the current time. To do that, I\'ll use the "current_time" function to fetch the most up-to-date information for you.', type='text'), ToolUseBlock(id='toolu_01A7BjS3dLRP18e2cS3YKhkF', input={}, name='current_time', type='tool_use')]}, {'role': 'user', 'content': [{'tool_use_id': 'toolu_01A7BjS3dLRP18e2cS3YKhkF', 'content': '"2024-07-17T19:45:57.566838-07:00"', 'type': 'tool_result'}]}, {'role': 'assistant', 'content': [TextBlock(text="\n\nBased on the information I've received, the current time is July 17, 2024, at 7:45:57 PM Pacific Daylight Time (PDT).\n\nIs there anything else you'd like to know or any other way I can assist you?", type='text')]}, {'role': 'user', 'content': "that's all, thank you!"}, {'role': 'assistant', 'content': [TextBlock(text="You're welcome! I'm glad I could help you with the current time. If you need any further assistance in the future, whether it's checking the time again or help with any other tasks, please don't hesitate to ask. Have a great rest of your day!", type='text')]}]

def render_messages(messages, provider):
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
