import streamlit as st
from toolhouse.models import OpenAIStream, stream_to_chat_completion
from types import SimpleNamespace

def anthropic_stream(response):
    for chunk in response.text_stream:
        yield chunk

def openai_stream(response, completion):
    for chunk in response:
        yield chunk
        completion.add(chunk)

def openai_render_tool_call(message):
    msg = ["**Using tools**"]
    for tool in message["tool_calls"]:
        args = tool["function"]["arguments"] if tool["function"]["arguments"] != "{}" else ""
        msg.append(f'```{tool["function"]["name"]}({args})```')

    return "\n\n".join(msg)

def print_messages(messages, provider):
    for message in messages:
        if provider == "anthropic":
            if isinstance(message["content"], str):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            elif isinstance(message["content"], list):
                has_tool = False
                msg = []
                for m in message["content"]:
                    if not hasattr(m, "type"):
                        continue
                    elif m.type == "text":
                        msg.append(m.text)
                    elif m.type == "tool_use":
                        if not has_tool:
                            msg.append("**Using tools**")
                        args = str(m.input) if str(m.input) != "{}" else ""
                        msg.append(f"```{m.name}({args})```")
                        has_tool = True

                if msg:
                    with st.chat_message(message["role"]):
                        st.markdown("\n\n".join(msg))
        else:
            if isinstance(message.get("tool_calls"), list):
                with st.chat_message("assistant"):
                    st.markdown(openai_render_tool_call(message))

            elif message["role"] != "tool":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

def append_and_print(response, role = "assistant"):
    with st.chat_message(role):
        if st.session_state.provider == 'anthropic':
            if st.session_state.stream:
                r = st.write_stream(anthropic_stream(response))
                st.session_state.messages.append({ "role": role, "content": response.get_final_message().content })
                message = response.get_final_message()
                
                has_tool = False
                msg = []
                for m in message.content:
                    if hasattr(m, "type") and m.type == "tool_use":
                        has_tool = True
                        args = str(m.input) if str(m.input) != "{}" else ""
                        msg.append(f"```{m.name}({args})```")
                
                if has_tool:
                    msg = ["**Using tools**"] + msg
                    st.markdown("\n\n".join(msg))
                        
                return message
            else:
                if response.content is not None:
                    st.session_state.messages.append({"role": role, "content": response.content})
                    text = next((c.text for c in response.content if hasattr(c, "text")), '…')
                    st.markdown(text)

                    has_tool = False
                    msg = []
                    for m in response.content:
                        if hasattr(m, "type") and m.type == "tool_use":
                            has_tool = True
                            args = str(m.input) if str(m.input) != "{}" else ""
                            msg.append(f"```{m.name}({args})```")
                    
                    if has_tool:
                        msg = ["**Using tools**"] + msg
                        st.markdown("\n\n".join(msg))

                return response
        else:
            if st.session_state.stream:
                stream_completion = OpenAIStream()
                r = st.write_stream(openai_stream(response, stream_completion))
                completion = stream_to_chat_completion(stream_completion)

                if completion.choices and completion.choices[0].message.tool_calls:
                    st.session_state.messages.append(completion.choices[0].message.model_dump())
                    st.markdown(openai_render_tool_call(completion.choices[0].message.to_dict()))
                else:
                    st.session_state.messages.append({"role": role, "content": r})
                
                return stream_completion
            else:
                st.session_state.messages.append(response.choices[0].message.model_dump())
                if (text := response.choices[0].message.content) is not None:
                    st.markdown(text)
                elif response.choices[0].message.tool_calls:
                    st.markdown(openai_render_tool_call(response.choices[0].message.to_dict()))
                return response
