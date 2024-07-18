import os
from openai import OpenAI
from anthropic import Anthropic
from groq import Groq

llms = {
    "Claude 3.5 Sonnet": { 
        "provider": "anthropic", 
        "model": "claude-3-5-sonnet-20240620",
    },
    "GPT-4o": { 
        "provider": "openai", 
        "model": "gpt-4o", 
    },
    "Llama 70b-8192 (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama3-70b-8192", 
    },
    "Mixtral 8x7b (GroqCloud)": { 
        "provider": "openai", 
        "model": "mixtral-8x7b-32768", 
    },
    "Mixtral 8x7b (Together AI)": { 
        "provider": "openai", 
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1", 
    },
}

class LLMContextManager(object):
  def __init__(self, sdk):
    self.sdk = sdk
  
  def __enter__(self):
    return self.sdk
  
  def __exit__(self, *args):
    pass

def select_llm(provider, **kwargs):
  if "GroqCloud" in provider:
    return call_groq(**kwargs)
  elif "Together AI" in provider:
    return call_together(**kwargs)
  elif provider == "GPT-4o":
    return call_openai(**kwargs)
  elif provider == "Claude 3.5 Sonnet":
    return call_anthropic(**kwargs)
  else:
    raise Exception(f"Invalid LLM provider: {provider}")
  
def llm_call(provider, **kwargs):
  if not kwargs.get('stream', False):
    return LLMContextManager(select_llm(provider, **kwargs))
  else:
    return select_llm(provider, **kwargs)

def call_openai(**kwargs):
  client = OpenAI()
  return client.chat.completions.create(**kwargs)

def call_anthropic(**kwargs):
  client = Anthropic()
  
  if kwargs.get("stream"):
    args = kwargs.copy()
    del args["stream"]
    return client.messages.stream(**args)
  else:
    return client.messages.create(**kwargs)

def call_groq(**kwargs):
  client = Groq(api_key=os.environ.get("GROQCLOUD_API_KEY"))
  
  messages = []
  for message in kwargs.get("messages", []):
    msg = message.copy()
    if "function_call" in msg:
      del msg["function_call"]
      
    if "tool_calls" in msg and msg["tool_calls"] is None:
      del msg["tool_calls"]

    messages.append(msg)
  
  kwargs["messages"] = messages
  
  return client.chat.completions.create(**kwargs)
  
def call_together(**kwargs):
  client = OpenAI(
    api_key=os.environ.get('TOGETHER_API_KEY'),
    base_url="https://api.together.xyz/v1",
  )
      
  return client.chat.completions.create(**kwargs)