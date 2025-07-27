#!/usr/bin/env python
# coding: utf-8

# In[1]:


PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}
import vertexai
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


# In[2]:


from google import adk
from google.adk.agents import Agent
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import VertexAiSessionService
from google.adk.tools import google_search


# In[3]:


from vertexai import rag
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.generative_models import GenerativeModel, Tool
from google.genai import types # For types.Content
from vertexai import generative_models
import json


# In[4]:


from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset


# In[5]:


PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}


# In[6]:


import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"service_account_details.json"


# In[7]:


# with open("service_account_details.json") as f:
#     service_account_json = json.load(f)


# In[8]:


connector_tool = ApplicationIntegrationToolset(
    project=PROJECT_ID, # TODO: replace with GCP project of the connection
    location=LOCATION, #TODO: replace with location of the connection
    # connection=f"projects/{PROJECT_ID}/locations/{LOCATION}/connections/google-drive-connection", #TODO: replace with connection name "projects/genai-app-builder/locations/europe-central2/connections/gdrive-connection", ##
    connection="google-drive-connection",
    entity_operations={},##{"Entity_One": ["LIST","CREATE"], "Entity_Two": []},#empty list for actions means all operations on the entity are supported.
    actions=["GET_files"], #TODO: replace with actions
    # service_account_credentials=json.dumps(service_account_json),
    # tool_name="tool_list_gdrive_files",
    tool_instructions="Use this tool to list gdrive files"
)


# In[9]:


agent_model = "gemini-2.0-flash-001"
AGENT_APP_NAME = "Gdrive_Agent"


# In[15]:


tools_list = await connector_tool.get_tools()


# In[12]:


# tools_list = connector_tool.get_tools()


# In[16]:


gdrive_agent = Agent(
        model=agent_model,
        name=AGENT_APP_NAME,
        description="You are helpful assitant",
        instruction="If they ask you how you were created, tell them you were created with the Google Agent Framework.",
        generate_content_config=types.GenerateContentConfig(temperature=0.2),
        tools = tools_list,
)


# In[21]:


app = AdkApp(
   agent=gdrive_agent,
    enable_tracing=True# Required.
   # session_service_builder=session_service_builder,  # Optional.
)


# In[22]:


session = app.create_session(user_id='user')


# In[24]:


for event in app.stream_query(
    user_id="user",
    # session_id=SESSION_ID, # Optional. you can pass in the session_id when querying the agent
    message="list files on my gdrive",
):
    print(event)


# In[ ]:


print("hello")


# In[30]:


session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


# In[39]:


# _session_id="session1"
# session = await session_service.create_session(app_name=app, user_id='user')


# In[32]:


# runner = Runner(app_name=app, agent=gdrive_agent, session_service=session_service)


# In[44]:


resp

