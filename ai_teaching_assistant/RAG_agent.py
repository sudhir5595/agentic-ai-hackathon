

from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool
import vertexai

PROJECT_ID = "formidable-feat-466408-r6"  # @param {type:"string"}
LOCATION = "us-central1"  # @param {type:"string"}

vertexai.init(project=PROJECT_ID, location=LOCATION)


# Create RagCorpus
# Configure embedding model, for example "text-embedding-005".
embedding_model_config = rag.RagEmbeddingModelConfig(
    vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
        publisher_model="publishers/google/models/text-embedding-005"
    )
)


display_name="all-marathi-books"

rag_corpus = rag.create_corpus(
    display_name=display_name,
    backend_config=rag.RagVectorDbConfig(
        rag_embedding_model_config=embedding_model_config
    ),
)

rag_corpus.name


paths = ["gs://agentic_ai_ebooks_bucket/Books"]


# Import Files to the RagCorpus
import time

start_time = time.time()

rag.import_files(
    rag_corpus.name,
    paths,
    # Optional
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=512,
            chunk_overlap=100,
        ),
    ),
    max_embedding_requests_per_min=1000,  # Optional
)

end_time = time.time()

print("Total time to build the indexing", end_time-start_time)




rag.list_files(rag_corpus.name)



# Direct context retrieval
rag_retrieval_config = rag.RagRetrievalConfig(
    top_k=3,  # Optional
    filter=rag.Filter(vector_distance_threshold=0.5),  # Optional
)
response = rag.retrieval_query(
    rag_resources=[
        rag.RagResource(
            rag_corpus=rag_corpus.name,
            # Optional: supply IDs from `rag.list_files()`.
            # rag_file_ids=["rag-file-1", "rag-file-2", ...],
        )
    ],
    text="What is RAG and why it is helpful?",
    rag_retrieval_config=rag_retrieval_config,
)

# Direct context retrieval
rag_retrieval_config = rag.RagRetrievalConfig(
    top_k=3,  # Optional
    filter=rag.Filter(vector_distance_threshold=0.5),  # Optional
)


rag_retrieval_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(
            rag_resources=[
                rag.RagResource(
                    rag_corpus='projects/44474009687/locations/us-central1/ragCorpora/6917529027641081856',  # Currently only 1 corpus is allowed.
                    # Optional: supply IDs from `rag.list_files()`.
                    # rag_file_ids=["rag-file-1", "rag-file-2", ...],
                )
            ],
            rag_retrieval_config=rag_retrieval_config,
        ),
    )
)



# Create a Gemini model instance
rag_model = GenerativeModel(
    model_name="gemini-2.0-flash-001", tools=[rag_retrieval_tool]
)

# Generate response
response = rag_model.generate_content("What are the 21st century skills")
print(response.text)



# Generate response
response = rag_model.generate_content("Help me to summarize the ala paus ala poem")
print(response.text)


# Generate response
response = rag_model.generate_content("Help me to prepare a content for class 1 from balbharati part 1 for the first week of the school")
print(response.text)



# Generate response
response = rag_model.generate_content("Help me to summarize the ala paus ala")
print(response.text)



# Generate response
response = rag_model.generate_content("Help me to summarize the Mazya ya otivar")
print(response.text)


# Generate response
response = rag_model.generate_content("What are the six thinking hats")
print(response.text)

# Generate response
response = rag_model.generate_content("Help me to summarize the gadi ali gadi ali poem")
print(response.text)


# Generate response
response = rag_model.generate_content("I am teacher who teaches for the 1st standard students. Help me to generate the content for the first month of the school")
print(response.text)

# Generate response
response = rag_model.generate_content("I am teacher who teaches for the 1st standard students. Help me to generate the quiz for the first chapter of the part 1 book")
print(response.text)




