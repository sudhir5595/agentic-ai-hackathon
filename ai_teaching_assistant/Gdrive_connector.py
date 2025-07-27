#!/usr/bin/env python
# coding: utf-8

# Standard library imports
import os
import json

# Third-party imports
from google import adk
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, Session, VertexAiSessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.genai import types
from google.genai.types import Content, Part
from vertexai import agent_engines, rag, generative_models
from vertexai.generative_models import GenerativeModel, Tool
from vertexai.preview.reasoning_engines import AdkApp

# Constants
PROJECT_ID = "formidable-feat-466408-r6"  # GCP Project ID
LOCATION = "us-central1"  # GCP Location
STAGING_BUCKET = "gs://agentic_ai_ebooks_bucket"  # GCP Staging Bucket

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Application Integration Toolset Configuration
connector_tool = ApplicationIntegrationToolset(
    project=PROJECT_ID,
    location=LOCATION,
    connection="google-drive-connection",
    entity_operations={},
    actions=["GET_files"],
    tool_instructions="Use this tool to list gdrive files"
)

# Agent Configuration
agent_model = "gemini-2.0-flash-001"
AGENT_APP_NAME = "Gdrive_Agent"
tools_list = await connector_tool.get_tools()

gdrive_agent = Agent(
    model=agent_model,
    name=AGENT_APP_NAME,
    description="You are a helpful assistant",
    instruction="If they ask you how you were created, tell them you were created with the Google Agent Framework.",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=tools_list,
)

# ADK Application Configuration
app = AdkApp(
    agent=gdrive_agent,
    enable_tracing=True
)

# Create Session
session = app.create_session(user_id="user")

# Stream Query
for event in app.stream_query(
    user_id="user",
    message="list files on my gdrive",
):
    print(event)

# Vertex AI Session Service
session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)

