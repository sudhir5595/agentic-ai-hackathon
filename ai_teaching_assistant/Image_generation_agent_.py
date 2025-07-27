#!/usr/bin/env python
# coding: utf-8

# In[2]:


PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}
import vertexai
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)


# In[3]:


from datetime import datetime
from google import adk
from google.adk.agents import Agent
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import VertexAiSessionService
from google.adk.tools import google_search
from google.adk.tools import LongRunningFunctionTool
from google.adk.tools import ToolContext


# In[4]:


from vertexai import rag
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.generative_models import GenerativeModel, Tool
from google.genai import types # For types.Content
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai import generative_models
import json
import io
from google.cloud import storage


# In[5]:


import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"]="1"
os.environ["GOOGLE_CLOUD_PROJECT"]="formidable-feat-466408-r6"
os.environ["GOOGLE_CLOUD_LOCATION"]="us-central1"


# In[6]:


from google import genai
client = genai.Client()


# In[7]:


# Save to GCS bucket
# def upload_to_gcs():
#     """
#     Uploads a file to the GCS bucket - no input is needed.
    
#     Returns:
#         str: Public URL of the uploaded file.
#     """
    
#     bucket_name = "agentic_ai_ebooks_bucket"
#     source_file_name = "sample_image.png"
#     destination_blob_name = "uploaded_images/sample_image.png"
    
#     try:
#         # Initialize the GCS client
#         storage_client = storage.Client()

#         # Get the bucket
#         bucket = storage_client.bucket(bucket_name)

#         # Create a blob object
#         blob = bucket.blob(destination_blob_name)

#         # Upload the file
#         blob.upload_from_filename(source_file_name)

#         print(f"File {source_file_name} uploaded to {destination_blob_name} in bucket {bucket_name}.")
        
#         # Return the public URL of the uploaded file
#         return blob.public_url

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None
# if __name__ == "__main__":
#     # Example usage
    

#     public_url = upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
#     if public_url:
#         print(f"File uploaded successfully. Public URL: {public_url}")
#     else:
#         print("File upload failed.")


# In[8]:


# Define the image generation tool
async def generate_image(prompt: str, tool_context: ToolContext):
    """Generates an image based on the given prompt using Imagen.
     Returns:
        str: Public URL of the uploaded file.
    """
    
    response = client.models.generate_images(
        prompt=prompt,
        model="imagen-3.0-generate-002",
        config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_few",
                person_generation="allow_all",
            )
    )
    
    
    if response.generated_images is not None:
        for generated_image in response.generated_images:
            # Get the image bytes
            image_bytes = generated_image.image.image_bytes
            counter = str(tool_context.state.get("loop_iteration", 0))
            artifact_name = f"generated_image_" + counter + ".png"
            # call save to gcs function
            # if config.GCS_BUCKET_NAME:
            save_to_gcs(tool_context, image_bytes, artifact_name, counter)
            
         # Save as ADK artifact (optional, if still needed by other ADK components)
            report_artifact = types.Part.from_bytes(
                data=image_bytes, mime_type="image/png"
            )

            await tool_context.save_artifact(artifact_name, report_artifact)
            print(f"Image also saved as ADK artifact: {artifact_name}")

            return {
                "status": "success",
                "message": f"Image generated .  ADK artifact: {artifact_name}.",
                "artifact_name": artifact_name,
            }

    
    # images[0].save("sample_image.png")
    

#     bucket_name = "agentic_ai_ebooks_bucket"
#     source_file_name = "sample_image.png"
#     destination_blob_name = "uploaded_images/sample_image.png"

#     try:
#         # Initialize the GCS client
#         storage_client = storage.Client()

#         # Get the bucket
#         bucket = storage_client.bucket(bucket_name)

#         # Create a blob object
#         blob = bucket.blob(destination_blob_name)

#         # Upload the file
#         blob.upload_from_filename(source_file_name)

#         print(f"File {source_file_name} uploaded to {destination_blob_name} in bucket {bucket_name}.")

#         # Return the public URL of the uploaded file
#         return blob.public_url

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None
    
#     # public_url = upload_to_gcs()
    
#     return None


# In[9]:


def save_to_gcs(tool_context: ToolContext, image_bytes, filename: str, counter: str):
    # --- Save to GCS ---
    storage_client = storage.Client()  # Initialize GCS client
    bucket_name = "agentic_ai_ebooks_bucket"

    unique_id = tool_context.state.get("unique_id", "")
    current_date_str = datetime.utcnow().strftime("%Y-%m-%d")
    unique_filename = filename
    gcs_blob_name = f"{current_date_str}/{unique_id}/{unique_filename}"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_blob_name)

    try:
        blob.upload_from_string(image_bytes, content_type="image/png")
        gcs_uri = f"gs://{bucket_name}/{gcs_blob_name}"

        # Store GCS URI in session context
        # Store GCS URI in session context
        tool_context.state["generated_image_gcs_uri_" + counter] = gcs_uri

    except Exception as e_gcs:

        # Decide if this is a fatal error for the tool
        return {
            "status": "error",
            "message": f"Image generated but failed to upload to GCS: {e_gcs}",
        }
        # --- End Save to GCS ---


# In[10]:


# long_running_tool = LongRunningFunctionTool(func=generate_image)


# In[11]:


agent_model = "gemini-2.0-flash-001"
AGENT_APP_NAME = "Image_generation_agent"


# In[12]:


image_generation_agent = Agent(
        model=agent_model,
        name=AGENT_APP_NAME,
        description="You are helpful assitant, which help users to generate the images",
        instruction="You are an AI assistant designed to help teachers create visual aids for students. Your primary goal is to generate images that support educational activities and enhance learning.When generating an image, ensure it aligns with the following principles derived from educational practices:Encourage Observation: Create visuals that prompt students to look closely and observe details (निरीक्षण कर).Promote Action: Design images that can be used for look and do (बघ व कर) activities.Foster Creativity (सर्जनशीलता): Your visuals should inspire creative thinking and can be used for exercises like Picture Brainstorming or Thinker Keys.Be a Learning Medium (माध्यम): Function as a piece of educational technology (तंत्रज्ञान) that makes concepts clearer. Support Activities: If requested, generate simple outlines suitable for activities like fill the colours (रंग भर). Always generate content that is clear, simple, and appropriate for a student audience.",
        generate_content_config=types.GenerateContentConfig(temperature=0.2),
        tools = [generate_image],
)


# In[13]:


# Define an ADK agent
root_agent = adk.Agent(
    model="gemini-2.0-flash",
    name='my_agent',
    instruction="You are an helpful Agent",
)


# In[14]:


app = AdkApp(
   agent=image_generation_agent,
    enable_tracing=True# Required.
   # session_service_builder=session_service_builder,  # Optional.
)


# In[15]:


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


# In[ ]:





# In[26]:


# await query_agent(remote_agent)


# In[27]:


# This will create a session locally for interaction
session = app.create_session(user_id="123")
for event in app.stream_query(
    user_id="123",
    session_id=session.id,
    message="Generate me any mobile phone image",
):
    print(event)


# In[16]:


display_name = "Image_Generation_Agent"
description = "An agent that will generate the images based on the user query"


# In[18]:


remote_agent = agent_engines.create(
    app,
    requirements=[
        "google-adk (>=0.0.2)",
        "google-cloud-aiplatform[agent_engines] (>=1.88.0,<2.0.0)",
        "google-genai (>=1.5.0,<2.0.0)",
        "pydantic (>=2.10.6,<3.0.0)",
        "absl-py (>=2.2.1,<3.0.0)",
        "google-cloud-storage(>=2.14.0,<=3.1.0)",
        "pillow (>=10.3.0,<11.0.0)",
    ],
    display_name=display_name,
    description=description
)


# In[41]:


resource_name='projects/formidable-feat-466408-r6/locations/us-central1/reasoningEngines/1369753993697296384'

remote_agent = agent_engines.update(
    agent_engine=app,
    resource_name=resource_name,
    requirements=[
        "google-adk (>=0.0.2)",
        "google-cloud-aiplatform[agent_engines] (>=1.91.0,!=1.92.0)",
        "google-genai (>=1.5.0,<2.0.0)",
        "pillow",
        "pydantic (>=2.10.6,<3.0.0)"
    ],
    display_name=display_name,
    description=description
)


# In[15]:


# Step 8: Query the Agent
async def query_agent(remote_agent):
    async for event in remote_agent.stream_query(
        user_id="1",
        message="Generate an image of a wooden table",
    ):
        print(event)


# In[17]:


query_agent(remote_agent)


# In[19]:


for event in remote_agent.stream_query(
    user_id="1",
    # session_id=SESSION_ID, # Optional. you can pass in the session_id when querying the agent
    message="Generate the image of any wooden table",
):
    print(event)


# In[35]:


PROJECT_ID = "formidable-feat-466408-r6"
LOCATION = "us-central1"
# The app_name used with this service should be the Reasoning Engine ID or name
REASONING_ENGINE_APP_NAME = "projects/44474009687/locations/us-central1/reasoningEngines/1369753993697296384"

session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


# In[43]:


runner = adk.Runner(
    agent=root_agent,
    app_name=REASONING_ENGINE_APP_NAME,
    session_service=session_service)


# In[44]:


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


# In[45]:


temp_session = new_session


# In[46]:


# Helper method to send query to the runner
def call_agent(query, session_id, user_id):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(
      user_id=user_id, session_id=session_id, new_message=content)
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


# In[49]:


user_input = "Generate the wooden table image"


# In[50]:


call_agent(user_input, temp_session.id, temp_session.user_id)


# In[109]:


# session = app.create_session(user_id='user')


# In[114]:


# for event in app.stream_query(
#     user_id="user",
#     # session_id=SESSION_ID, # Optional. you can pass in the session_id when querying the agent
#     message="Generate a laptop image",
# ):
#     print(event)
    # image_op.append(event)


# In[ ]:




