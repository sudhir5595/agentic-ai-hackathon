"""
This module initializes and configures an AI agent for educational purposes.
The agent interacts with users based on predefined instructions and tools.
"""

# Standard Library Imports
import warnings
from typing import Optional, Sequence

# Third-Party Imports
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from google.genai import types  # For types.Content
from google.adk.sessions import InMemorySessionService, Session, VertexAiSessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.adk.agents import Agent
from vertexai import agent_engines, generative_models, rag
from vertexai.preview.reasoning_engines import AdkApp
from IPython.display import HTML, Markdown, display

# Constants
PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # @param {type:"string"}

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Agent Model Configuration
agent_model = "gemini-2.0-flash-001"

# Safety Settings
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]

# RAG Resource Name
rag_resource_name = "projects/formidable-feat-466408-r6/locations/us-central1/ragCorpora/4749045807062188032"

# RAG Retrieval Tool
rag_retrieval_tool = VertexAiRagRetrieval(
    name="retrieve_rag_documentation",
    description=(
        "Use this tool to retrieve documentation and reference materials for the question from the RAG corpus."
    ),
    rag_resources=[
        rag.RagResource(
            rag_corpus=rag_resource_name
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)

# Agent Configuration
agent = Agent(
    model=agent_model,
    name="Classroom_Agent",
    instruction=(
        """A personalized AI learning assistant for Balbharati and Grade first to fifth standard.
        This agent serves to help students understand concepts, review material, and prepare for assessments.
        Its knowledge is strictly limited to the content within the official course textbook(s).
        This agent will be used by teachers."""
    ),
    description=(
        """# CORE IDENTITY
        - You are an AI learning agent, an expert AI tutor for Grade first to fifth standard.
        - Your designated persona is to help students and will be used by teachers. Maintain this tone and interaction style consistently.
        # KNOWLEDGE GROUNDING (ABSOLUTE DIRECTIVE)
        - Your knowledge base is STRICTLY and EXCLUSIVELY limited to the content of the document provided to you.
        - You MUST base all of your answers, explanations, and examples on information found within these source materials.
        - If a question cannot be answered using the provided texts, you MUST state that clearly.
        - DO NOT, under any circumstances, use external knowledge, access the general internet, or invent information.
        # CITATION REQUIREMENT
        - For every answer you provide, cite the specific location in the source material where the information was found.
        # INTERACTION PROTOCOL
        - Your primary goal is to help students learn, not to give them shortcuts.
        - Engage with students based on your persona.
        - Adhere to the following specific behavioral rules:
            - Answer the question in the local language of the textbooks.
            - If specifically asked to generate in English, then only generate in English.
        # SCOPE AND SAFETY
        - Politely decline to answer questions that are off-topic, personal, or outside the academic scope of the subject.
        - Do not engage in debates or express opinions. Your function is to relay and explain the information from your source texts."""
    ),
    tools=[rag_retrieval_tool],
)

# ADK Application
app = AdkApp(
    agent=agent,
    enable_tracing=True,  # Required.
)

# Create a Session
session = app.create_session(user_id="123")
for event in app.stream_query(
    user_id="123",
    session_id=session.id,
    message="hello!",
):
    if event.get("content", None):
        print("Agent created successfully")

# Display Session
print(session)

# Remote Agent Deployment
remote_agent = agent_engines.create(
    app,
    requirements=[
        "google-adk (>=0.0.2)",
        "google-cloud-aiplatform[agent_engines] (>=1.91.0,!=1.92.0)",
        "google-genai (>=1.5.0,<2.0.0)",
        "llama-index",
        "pydantic (>=2.10.6,<3.0.0)"
    ],
    display_name="School_Agent",
    description="An agent that has access to the classroom RAG engine",
)

# Query Remote Agent
for event in remote_agent.stream_query(
    user_id="1",
    message="What are your capabilities?",
):
    print(event)

