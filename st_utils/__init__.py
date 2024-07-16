class Chat:
    def __init__(self, st, provider: str = "openai", stream: bool = False):
        self.st = st
        self.provider = provider
        self.stream = stream
      
    def anthropic_stream(self, response):
        for chunk in response:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text

    def append(self, obj):
        self.st.session_state.messages.append(obj)
        
    def messages(self):
        return self.st.session_state.messages

    def append_and_print(self, response, role = "assistant"):
        with self.st.chat_message(role):
            if self.provider == 'anthropic':
                if self.stream:
                    r = self.st.write_stream(self.anthropic_stream(response))
                    self.st.session_state.messages.append({ "role": role, "content": r })
                    response.close()
                else:
                    if response.content is not None:
                        self.st.session_state.messages.append({"role": role, "content": response.content})
                        text = next((c.text for c in response.content if hasattr(c, "text")), '…')
                        self.st.write(text)
            else:
                if self.stream:
                    r = self.st.write_stream(response)
                    self.st.session_state.messages.append({ "role": role, "content": r })
                else:
                    self.st.session_state.messages.append(response.choices[0].message.model_dump())
                    if (text := response.choices[0].message.content) is not None:
                        self.st.write(text)
                    elif response.choices[0].message.tool_calls:
                        tool_calls = response.choices[0].message.tool_calls
                        tools = [t.function.name for t in tool_calls]
                        self.st.write(f"Calling: " + ", ".join(tools))

    def print_chat(self):
        for message in self.st.session_state.messages:
            with self.st.chat_message(message["role"]):
                if self.provider == 'anthropic':
                    text = next(c.text for c in message["content"] if hasattr(c, "text")) if message["role"] == "assistant" else message["content"]
                    self.st.markdown(text)
                else:
                    self.st.markdown(message["content"])