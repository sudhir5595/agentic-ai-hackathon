
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


import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"]="1"
os.environ["GOOGLE_CLOUD_PROJECT"]="formidable-feat-466408-r6"
os.environ["GOOGLE_CLOUD_LOCATION"]="us-central1"


PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}

import vertexai

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)



sahayak_agent = agent_engines.get('projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720')


session = sahayak_agent.create_session(user_id="3")

# List the session
session = sahayak_agent.list_sessions(user_id='memory_test_4')

user_input = "list the prompts given to you"
session = session['sessions'][0]


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



PROJECT_ID = "formidable-feat-466408-r6"
LOCATION = "us-central1"
# The app_name used with this service should be the Reasoning Engine ID or name
REASONING_ENGINE_APP_NAME = "projects/44474009687/locations/us-central1/reasoningEngines/7395007345165598720"

session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


user_input = "Help me to get the stock value of the General Mills"



# Define an ADK agent
root_agent = adk.Agent(
    model="gemini-2.0-flash",
    name='my_agent',
    instruction="You are an helpful Agent",
    # tools=[greetings]
)

runner = adk.Runner(
    agent=root_agent,
    app_name=REASONING_ENGINE_APP_NAME,
    session_service=session_service)



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



temp_session = new_session

# Helper method to send query to the runner
def call_agent(query, session_id, user_id):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(
      user_id=user_id, session_id=session_id, new_message=content)
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


user_input = "What is the meaning of ADK"

call_agent(user_input, temp_session.id, temp_session.user_id)

