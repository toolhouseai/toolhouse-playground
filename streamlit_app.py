import streamlit as st
from openai import OpenAI
import requests
import json
import os

def send_email(api_key, domain, sender, recipient, subject, body):


    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ("api", api_key)
    data = {
        "from": sender,
        "to": recipient,
        "subject": subject,
        "text": body
    }

    response = requests.post(url, auth=auth, data=data)
    
    if response.status_code == 200:
        return "Email sent successfully!"
    else:
        return f"Failed to send email: {response.status_code} - {response.text}"

st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4o model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

#openai_api_key = os.getenv("OPENAI_API_KEY")

openai_api_key = st.text_input("OpenAI API Key", type="password")
mailgun_api_key = st.text_input("Mailgun API Key", type="password")
mailgun_domain = st.text_input("Mailgun Domain", type="default")
if not openai_api_key or not mailgun_api_key or not mailgun_domain:
    st.info("Please add your API key(s)/info to continue.", icon="🗝️")
else:

    client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        functions = [
            {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email using the Mailgun API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "api_key": {"type": "string", "description": "Mailgun API key"},
                        "domain": {"type": "string", "description": "Mailgun domain"},
                        "sender": {"type": "string", "description": "Sender email address"},
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Subject of the email"},
                        "body": {"type": "string", "description": "Body of the email"}
                    },
                    "required": ["api_key", "domain", "sender", "recipient", "subject", "body"]
                }
            }
            }
        ]
        msgs = [
            {"role": "system", "content": "You are a helpful assistant that can chat with a user and send emails."},
            {"role": "assistant", "content": "My sender email address is 'mailgun@sandboxe3ee30865707422a8f4ce9da59bc9c8c.mailgun.org'."},
            ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            stream=False,
            tools=functions,
            tool_choice="auto",
        ) # type: ignore

        if stream.choices[0].message.tool_calls is not None:
            function_call_name = stream.choices[0].message.tool_calls[0].function.name
            tool_call_id = stream.choices[0].message.tool_calls[0].id
            tool_function_name = stream.choices[0].message.tool_calls[0].function.name
            if function_call_name == "send_email":
                arguments = json.loads(stream.choices[0].message.tool_calls[0].function.arguments)
                result = send_email(
                    api_key=mailgun_api_key,
                    domain=mailgun_domain,
                    sender=arguments['sender'],
                    recipient=arguments['recipient'],
                    subject=arguments['subject'],
                    body=arguments['body']
                )
                msgs.append({
                    "role":"assistant", 
                    "tool_call_id":tool_call_id, 
                    "name": tool_function_name, 
                    "content":f"You successfully sent an email because the API returned this result {result}, let the user know that you sent the email to the recipient and tell them which recipient."
                })
                model_response_with_function_call = client.chat.completions.create(
                    model="gpt-4o",
                    messages=msgs,
                )  
                st.session_state.messages.append({"role": "assistant", "content": model_response_with_function_call.choices[0].message.content})
                with st.chat_message("assistant"):
                    if model_response_with_function_call.choices[0].message.content is not None:
                        response = model_response_with_function_call.choices[0].message.content
                        st.write(response)
        else:
            with st.chat_message("assistant"):
                if stream.choices[0].message.content is not None:
                    response = stream.choices[0].message.content
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})