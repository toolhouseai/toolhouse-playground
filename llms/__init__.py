import os
from openai import OpenAI
from anthropic import Anthropic
from groq import Groq

system_prompt="""You are a helpful assistant built by Toolhouse. You have advanced tools at your disposal:

- a tool that gives you the current time
- a tool to retrieve information about the user, such as preferences or things the user told you to remember
- a tool to send emails 

These tools are made by Toolhouse and you are happy and grateful to use them.

Execute the user tasks as you usually do. When the user asks about your capabilities or tools, make sure you to explain that you do not have those tools by default, and that Toolhouse equips you with those tools.

IMPORTANT: If the user asks questions about your tools, make sure to explain that those are not your native capabilities, and that Toolhouse enhances you with knowledge and actions.
<example>
User: wait, you can send emails?
Assistant: I now can, thanks to Toolhouse! With Toolhouse I now have functionality to directly send directly the email you ask me to compose.
</example>

When using the time tool, format the time in a user friendly way.
"""

llms = {
    "GPT-4o mini": { 
        "provider": "openai", 
        "model": "gpt-4o-mini", 
    },
    "GPT-4o": { 
        "provider": "openai", 
        "model": "gpt-4o", 
    },
    "Claude 3.5 Sonnet": { 
        "provider": "anthropic", 
        "model": "claude-3-5-sonnet-20240620",
    },
    "Claude 3 Haiku": { 
        "provider": "anthropic", 
        "model": "claude-3-haiku-20240307",
    },
    "Claude 3 Sonnet": { 
        "provider": "anthropic", 
        "model": "claude-3-sonnet-20240229",
    },
    "Claude 3 Opus": { 
        "provider": "anthropic", 
        "model": "claude-3-opus-20240229",
    },
    "Llama 3.1 70B (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama-3.1-70b-versatile", 
    },
    "Llama 3.1 8B (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama-3.1-8b-instant", 
    },
    "Llama 3 70b-8192 (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama3-groq-70b-8192-tool-use-preview", 
    },
    "Llama 3 8b-8192 (GroqCloud)": { 
        "provider": "openai", 
        "model": "llama3-groq-8b-8192-tool-use-preview", 
    },
    "Mixtral 8x7b (GroqCloud)": { 
        "provider": "openai", 
        "model": "mixtral-8x7b-32768", 
    },
    "Gemma2 9b (GroqCloud)": { 
        "provider": "openai", 
        "model": "gemma2-9b-it", 
    },
    "Gemma 7b (GroqCloud)": { 
        "provider": "openai", 
        "model": "gemma-7b-it", 
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
  elif provider == "GPT-4o" or provider == "GPT-4o mini":
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
  args = kwargs.copy()
  
  if not next((m["role"] == "system" for m in args["messages"]), None):
      args["messages"] = [{"role": "system", "content": system_prompt}] + args["messages"]
  
  return client.chat.completions.create(**args)

def call_anthropic(**kwargs):
  client = Anthropic()
  args = kwargs.copy()
  args["system"] = system_prompt
  
  if kwargs.get("tools") is None:
    del args["tools"]
  
  if kwargs.get("stream"):
    del args["stream"]
    return client.messages.stream(**args)
  else:
    return client.messages.create(**args)    

def call_groq(**kwargs):
  client = OpenAI(
    api_key=os.environ.get('GROQCLOUD_API_KEY'),
    base_url="https://api.groq.com/openai/v1",
  )

  msgs = kwargs.get("messages", []).copy()
  if not next((m["role"] == "system" for m in msgs), None):
    msgs = [{"role": "system", "content": system_prompt}] + msgs
  
  messages = [{"role": "system", "content": system_prompt}]
  for message in msgs:
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