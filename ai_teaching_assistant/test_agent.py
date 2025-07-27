#!/usr/bin/env python
# coding: utf-8

# In[1]:


from vertexai import agent_engines
from vertexai.preview.reasoning_engines import LangchainAgent
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool,
    ToolConfig
)
from google import adk
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.adk.agents import LlmAgent, BaseAgent
import yaml
from google.genai import types # For types.Content
from typing import Optional
from typing import Sequence
from IPython.display import HTML, Markdown, display
import warnings


# In[2]:


import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"]="1"
os.environ["GOOGLE_CLOUD_PROJECT"]="formidable-feat-466408-r6"
os.environ["GOOGLE_CLOUD_LOCATION"]="us-central1"


# In[3]:


PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}

import vertexai

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


# ### Load the agent

# In[4]:


sahayak_agent = agent_engines.get('projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720')
# 'projects/44474009687/locations/us-central1/reasoningEngines/8877817522477334528'


# In[5]:


session = sahayak_agent.create_session(user_id="3")


# In[6]:


# List the session
session = sahayak_agent.list_sessions(user_id='memory_test_4')


# In[11]:


# user_input = "Which prompt was given to you earlier?"
user_input = "list the prompts given to you"


# In[7]:


session


# In[8]:


session = session['sessions'][0]


# In[9]:


session


# In[12]:


for event in sahayak_agent.stream_query(
            user_id=session['userId'], session_id=session['id'], message=user_input
        ):
            if "content" in event:
                if "parts" in event["content"]:
                    parts = event["content"]["parts"]
                    for part in parts:
                        if "text" in part:
                            text_part = part["text"]
                            print(f"Response: {text_part}")


# In[ ]:


# for event in sahayak_agent.stream_query(user_id=session.user_id, session_id.id, message=user_input):
#     session_service.append_event(session, event)
#     if "content" in event:
#         if "parts" in event["content"]:
#             parts = event["content"]["parts"]
#             for part in parts:
#                 if "text" in part:
#                     text_part = part["text"]
#                     print(f"Response: {text_part}")


# ### Test the Vertex AI session service

# In[24]:


PROJECT_ID = "formidable-feat-466408-r6"
LOCATION = "us-central1"
# The app_name used with this service should be the Reasoning Engine ID or name
REASONING_ENGINE_APP_NAME = "projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720"

session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


# In[ ]:


# session_test = session_service.get_session(app_name='sahayak_agent',user_id='1',session_id='2617280227537059840')


# In[ ]:


# session = await session_service.create_session(app_name=REASONING_ENGINE_APP_NAME,user_id='3')


# In[ ]:


user_input = "Help me to get the stock value of the General Mills"


# In[ ]:


# --- Setup Runner and Session ---
# async def setup_session_and_runner():
#     session_service = InMemorySessionService()
#     session = await session_service.create_session(app_name=REASONING_ENGINE_APP_NAME,user_id='memory_test_1')
#     logger.info(f"Initial session state: {session.state}")
#     runner = Runner(
#         agent=story_flow_agent, # Pass the custom orchestrator agent
#         app_name=APP_NAME,
#         session_service=session_service
#     )
#     return session_service, runner


# In[ ]:


# session_service, runner = await setup_session_and_runner()


# In[ ]:


# for event in sahayak_agent.stream_query(
#             user_id=session_service.user_id, session_id=session_service.id, message=user_input
#         ):
#             session_service.append_event()
#             if "content" in event:
#                 if "parts" in event["content"]:
#                     parts = event["content"]["parts"]
#                     for part in parts:
#                         if "text" in part:
#                             text_part = part["text"]
#                             print(f"Response: {text_part}")


# In[22]:


# Define an ADK agent
root_agent = adk.Agent(
    model="gemini-2.0-flash",
    name='my_agent',
    instruction="You are an helpful Agent",
    # tools=[greetings]
)


# In[23]:


runner = adk.Runner(
    agent=root_agent,
    app_name=REASONING_ENGINE_APP_NAME,
    session_service=session_service)


# In[13]:


# Create a session
# session = await session_service.create_session(
#        app_name=REASONING_ENGINE_APP_NAME,
#        user_id='memory_test_4')

#check for existing sessions
existing_sessions = await session_service.list_sessions(
    app_name = REASONING_ENGINE_APP_NAME,
    user_id = 'memory_test_6',
)

if existing_sessions and len(existing_sessions.sessions) > 0:
    SESSION_ID = existing_sessions.sessions[0].id
    print(f"Continuing existing session: {SESSION_ID}")
else:
    new_session = await session_service.create_session(
        app_name = REASONING_ENGINE_APP_NAME,
        user_id = 'memory_test_6',
    )
    SESSION_ID = new_session.id
    print(f"Created new session: {SESSION_ID}")


# In[16]:


# temp_session = existing_sessions.sessions[0]
temp_session = new_session


# In[17]:


temp_session


# In[25]:


# Helper method to send query to the runner
def call_agent(query, session_id, user_id):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(
      user_id=user_id, session_id=session_id, new_message=content)
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


# In[32]:


# user_input = "Help me to get the stock value of the Micron"
# user_input = "Help me to get the information about the weather in Pune"
# user_input = "Give me the list of travel destination near Mumbai"
user_input = "What is the meaning of ADK"


# In[33]:


call_agent(user_input, temp_session.id, temp_session.user_id)


# In[34]:


temp_session


# In[ ]:




