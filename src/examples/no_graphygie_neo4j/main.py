from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.generation.prompts import RagTemplate
from neo4j_graphrag.embeddings import OllamaEmbeddings
from dotenv import load_dotenv
from util import unwrap

import logging
import os

_ = load_dotenv()

NEO4J_URI = unwrap(os.getenv("NEO4J_URI"))
NEO4J_USERNAME = unwrap(os.getenv("NEO4J_USERNAME"))
NEO4J_PASSWORD = unwrap(os.getenv("NEO4J_PASSWORD"))
NEO4J_DATABASE = unwrap(os.getenv("NEO4J_DATABASE"))
NEO4J_EMBED_INDEX = unwrap(os.getenv("NEO4J_EMBED_INDEX"))

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))
EMBEDDING_MODEL = unwrap(os.getenv("EMBEDDING_MODEL"))

OPENAI_URI = unwrap(os.getenv("OPENAI_URI"))
OPENAI_TOKEN = unwrap(os.getenv("OPENAI_TOKEN"))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="{levelname}:{name}:\n{message}", style="{"
    )

    # Connect to Neo4j database
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )

    # 2. Retriever
    # Create Embedder object, needed to convert the user question (text) to a
    # vector
    embedder = OllamaEmbeddings(host=OLLAMA_URI, model=EMBEDDING_MODEL)

    # Initialize the retriever
    retriever = VectorRetriever(
        driver,
        NEO4J_EMBED_INDEX,
        embedder,
        neo4j_database=NEO4J_DATABASE,
    )

    # 3. LLM
    llm = OpenAILLM(
        base_url=OPENAI_URI,
        api_key=OPENAI_TOKEN,
        model_name="qwen/qwen3-235b-a22b:free",
        model_params={"temperature": 0},
    )

    # Initialize the RAG pipeline
    rag = GraphRAG(retriever=retriever, llm=llm)

    prompt_template = RagTemplate()
    prompt_template.DEFAULT_SYSTEM_INSTRUCTIONS = "Base your answer *primarily* on the information provided in the context below. If the context is empty or does not contain the necessary information to answer the question, use your internal knowledge."

    # Query the graph
    query_text = "What are the main cognitive and behavioral changes associated with Frontal Lobe Syndrome?"
    response = rag.search(
        query_text=query_text, retriever_config={"top_k": 5}, return_context=True
    )
    print(response.answer)
    print()
    print(response.retriever_result)


if __name__ == "__main__":
    main()
