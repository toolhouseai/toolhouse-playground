import os
from openai import OpenAI
from anthropic import Anthropic
from groq import Groq

llms = {
    "GPT-4o": { 
        "provider": "openai", 
        "model": "gpt-4o", 
    },
    "Claude 3.5 Sonnet": { 
        "provider": "anthropic", 
        "model": "claude-3-5-sonnet-20240620",
    },
    "Llama (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama3-70b-8192", 
    },
    "Mixtral (GroqCloud)": { 
        "provider": "openai", 
        "model": "mixtral-8x7b-32768", 
    },
}

def llm_call(provider, **kwargs):
  if "GroqCloud" in provider:
    return call_groq(**kwargs)
  elif provider == "GPT-4o":
    return call_openai(**kwargs)
  elif provider == "Claude 3.5 Sonnet":
    return call_anthropic(**kwargs)
  else:
    raise Exception(f"Invalid LLM provider: {provider}")
  
def call_openai(**kwargs):
  client = OpenAI()
  return client.chat.completions.create(
    model=kwargs.get("model"),
    messages=kwargs.get("messages"),
    stream=kwargs.get("stream"),
    tools=kwargs.get("tools"),
    max_tokens=kwargs.get("max_tokens"),
    tool_choice=kwargs.get("tool_choice"),
  )

def call_anthropic(**kwargs):
  client = Anthropic()
  return client.messages.create(
    model=kwargs.get("model"),
    messages=kwargs.get("messages"),
    stream=kwargs.get("stream"),
    tools=kwargs.get("tools"),
    max_tokens=kwargs.get("max_tokens"),
    tool_choice=kwargs.get("tool_choice"),
  )

def call_groq(**kwargs):
  client = Groq(api_key=os.environ.get('GROQCLOUD_API_KEY'))
  return client.chat.completions.create(
    model=kwargs.get("model"),
    messages=kwargs.get("messages"),
    stream=kwargs.get("stream"),
    tools=kwargs.get("tools"),
    max_tokens=kwargs.get("max_tokens"),
    tool_choice=kwargs.get("tool_choice"),
  )