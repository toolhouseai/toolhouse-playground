import streamlit as st
from openai import OpenAI
import requests

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4o model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        functions = [
            {
                "type": "function",
                "function": {
                    "name": "get_pokemon_info",
                    "description": "Get information about a specific Pokémon",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pokemon_name": {"type": "string", "description": "Name of the Pokémon"}
                        },
                        "required": ["pokemon_name"]
                    }
                }
            }
        ]
        msgs = [{"role": "system", "content": "You are a helpful assistant that can chat with a user and also fetch Pokémon information."}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            stream=False,
            tools=functions,
            tool_choice="auto"
        )

        function_call_name = stream.choices[0].message.tool_calls[0].function.name
        tool_call_id = stream.choices[0].message.tool_calls[0].id
        tool_function_name = stream.choices[0].message.tool_calls[0].function.name

        if function_call_name == "get_pokemon_info":
            arguments = json.loads(stream.choices[0].message.tool_calls[0].function.arguments)
            result = get_pokemon_info(arguments["pokemon_name"])
            msgs.append({
            "role":"assistant", 
            "tool_call_id":tool_call_id, 
            "name": tool_function_name, 
            "content":f"You successfully retrieved the following information about the requested pokemon: {result}"
            })
            model_response_with_function_call = client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            )
            st.session_state.messages.append({"role": "assistant", "content": model_response_with_function_call})

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = stream
        st.session_state.messages.append({"role": "assistant", "content": response})


# Useful functions

def get_pokemon_info(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        pokemon_info = {
            "name": data["name"],
            "id": data["id"],
            "height": data["height"],
            "weight": data["weight"],
            "types": [type_info["type"]["name"] for type_info in data["types"]],
            "abilities": [ability_info["ability"]["name"] for ability_info in data["abilities"]],
            "base_stats": {stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]}
        }
        return pokemon_info
    else:
        return f"Failed to get information: {response.status_code} - {response.text}"
