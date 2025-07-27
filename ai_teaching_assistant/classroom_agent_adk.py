
PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}
import vertexai
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


from google import adk
from google.adk.agents import Agent
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import VertexAiSessionService
from google.adk.tools import google_search

from vertexai import rag
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.generative_models import GenerativeModel, Tool
from vertexai import generative_models

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

import yaml
from typing import Optional
from typing import Sequence
from google.genai import types # For types.Content
from IPython.display import HTML, Markdown, display
import warnings


agent_model = "gemini-2.0-flash-001"


from google.genai import types

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]


# rag_resource_name = 'projects/44474009687/locations/us-central1/ragCorpora/6917529027641081856'
rag_resource_name = 'projects/formidable-feat-466408-r6/locations/us-central1/ragCorpora/4749045807062188032'


# In[24]:


rag_retrieval_tool = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description=(
        'Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,'
    ),
    rag_resources=[
        rag.RagResource(
            # please fill in your own rag corpus
            # here is a sample rag corpus for testing purpose
            # e.g. projects/123/locations/us-central1/ragCorpora/456
            rag_corpus=rag_resource_name
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)


# In[25]:


agent = Agent(
    model=agent_model,
    name="Classroom_Agent",
    instruction=("A personalized AI learning assistant for balbharati and Grade first to fifth standard. This agent serves to help students understand concepts, review material, and prepare for assessments. Its knowledge is strictly limited to the content within the official course textbook(s). This agent will be used by teachers"),
    # instruction=react_prompt,
    description=("# CORE IDENTITY \
-   You are AI learning agent an expert AI tutor for Grade first to fifth standard. \
-   Your designated persona is to help students and will be used by teachers. Maintain this tone and interaction style consistently.\
# KNOWLEDGE GROUNDING (ABSOLUTE DIRECTIVE) \
-   Your knowledge base is STRICTLY and EXCLUSIVELY limited to the content of the document provided to you. \
-   You MUST base all of your answers, explanations, and examples on information found within these source materials. \
-   If a question cannot be answered using the provided texts, you MUST state that clearly. For example, say: I cannot answer that question as the information is not available in 'Patterns of Interaction'. \
-   DO NOT, under any circumstances, use external knowledge, access the general internet, or invent information. Your reality is defined by the classroom books. You can use LLM capabilities to answer the question for educational purpose. \
# CITATION REQUIREMENT \
-   For every answer you provide, you can cite the specific location in the source material where the information was found (e.g., According to Chapter 3, Section 2 of '[Textbook Title]'...). This is non-negotiable and reinforces your grounding. \
# INTERACTION PROTOCOL \
-   Your primary goal is to help students learn, not to give them shortcuts. \
-   Engage with students based on your persona. If you are a 'Socratic Tutor,' ask follow-up questions to stimulate critical thinking. If you are a 'Study Buddy,' use encouraging and collaborative language. \
-   Adhere to the following specific behavioral rules: \
    -   Answer the question in the local language of the textbooks. \
    -   If specifically asked to generate in English then only generate in Elnglish language \
# SCOPE AND SAFETY \
-   Politely decline to answer questions that are off-topic, personal, or outside the academic scope of Subject. \
-   Do not engage in debates or express opinions. Your function is to relay and explain the information from your source texts."
    ),
    tools=[rag_retrieval_tool],  
)


# In[26]:


app = AdkApp(
   agent=agent,
    enable_tracing=True# Required.
   # session_service_builder=session_service_builder,  # Optional.
)


# In[27]:


# This will create a session locally for interaction
session = app.create_session(user_id="123")
for event in app.stream_query(
    user_id="123",
    session_id=session.id,
    message="hello!",
):
    if event.get("content", None):
        print(
            f"Agent created successfully"
        )


# In[28]:


session


# In[ ]:





# In[8]:


# def greetings(query: str):
#   """Tool to greet user."""
#   if 'hello' in query.lower():
#     return {"greeting": "Hello, world"}
#   else:
#     return {"greeting": "Goodbye, world"}

# # Define an ADK agent
# root_agent = adk.Agent(
#     model="gemini-2.0-flash",
#     name='my_agent',
#     instruction="You are an Agent that greet users, always use greetings tool to respond.",
#     tools=[greetings]
# )


# In[10]:


# session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


# In[26]:


# runner = adk.Runner(
#     agent=root_agent,
#     app_name='projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720',
#     session_service=session_service)


# In[23]:


# runner = adk.Runner(
#     agent=root_agent,
#     app_name='Test',
#     session_service=session_service)


# In[33]:


# Helper method to send query to the runner
# def call_agent(query, session_id, user_id):
#     content = types.Content(role='user', parts=[types.Part(text=query)])
#     events = runner.run(
#       user_id=user_id, session_id=session_id, new_message=content)
#     for event in events:
#         if event.is_final_response():
#             final_response = event.content.parts[0].text
#             print("Agent Response: ", final_response)


# In[18]:


# agent.name.split("/")[-1]


# In[18]:


# Create a session
# session = await session_service.create_session(
#        app_name='projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720',
#        user_id='memory_test_5')


# In[29]:


for event in app.stream_query(
    user_id="123",
    session_id=session.id,
    message="What instructions are given to you?",
):
    print(event)


# In[30]:


display_name = "School_Agent"
description = "An agent that has access to the classroom RAG engine"


# ### Agent Deployment

# In[31]:


remote_agent = agent_engines.create(
    app,
    requirements=[
        "google-adk (>=0.0.2)",
        "google-cloud-aiplatform[agent_engines] (>=1.91.0,!=1.92.0)",
        "google-genai (>=1.5.0,<2.0.0)",
        "llama-index",
        "pydantic (>=2.10.6,<3.0.0)"
    ],
    display_name=display_name,
    description=description
)


# In[16]:


# resource_name='projects/44474009687/locations/us-central1/reasoningEngines/2451743804173058048/operations/784364897738686464'

# remote_agent = agent_engines.update(
#     agent_engine=agent,
#     resource_name=resource_name,
#     display_name=display_name,
#     description=description
# )


# In[ ]:


# resource_name='projects/925341040009/locations/us-central1/reasoningEngines/719599574053814272'

# remote_agent = agent_engines.update(
#     agent_engine=agent,
#     resource_name=resource_name,
#     display_name=display_name,
#     description=description
# )


# In[18]:


remote_agent.


# In[32]:


for event in remote_agent.stream_query(
    user_id="1",
    # session_id=SESSION_ID, # Optional. you can pass in the session_id when querying the agent
    message="What are your capabilties?",
):
    print(event)


# In[ ]:


# remote_agent.delete()

