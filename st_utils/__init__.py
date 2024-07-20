import streamlit as st
from toolhouse.models import OpenAIStream, stream_to_chat_completion

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
                with st.chat_message("assistant"):
                    msg = ["**Using tools**"]
                    for tool in message["tool_calls"]:
                        args = tool["function"]["arguments"] if tool["function"]["arguments"] != "{}" else ""
                        msg.append(f'```{tool["function"]["name"]}({args})```')

                    st.markdown("\n\n".join(msg))

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
                    st.markdown(text)
                return response
        else:
            if st.session_state.stream:
                stream_completion = OpenAIStream()
                r = st.write_stream(openai_stream(response, stream_completion))
                completion = stream_to_chat_completion(stream_completion)

                if completion.choices and completion.choices[0].message.tool_calls:
                    msg = ["**Using tools**"]
                    for tool in completion.choices[0].message.tool_calls:
                        args = tool.function.arguments if tool.function.arguments != "{}" else ""
                        msg.append(f'```{tool.function.name}({args})```')

                    st.session_state.messages.append(completion.choices[0].message.model_dump())
                    st.markdown("\n\n".join(msg))
                else:
                    st.session_state.messages.append({"role": role, "content": r})
                
                return stream_completion
            else:
                st.session_state.messages.append(response.choices[0].message.model_dump())
                if (text := response.choices[0].message.content) is not None:
                    st.markdown(text)
                elif response.choices[0].message.tool_calls:
                    msg = ["**Using tools**"]
                    for tool in response.choices[0].message.tool_calls:
                        args = tool.function.arguments if tool.function.arguments != "{}" else ""
                        msg.append(f'```{tool.function.name}({args})```')

                    st.session_state.messages.append(response.choices[0].message.model_dump())
                    st.markdown("\n\n".join(msg))
                return response
