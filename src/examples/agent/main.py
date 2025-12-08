"""
Main entry point for the Graphygie pipeline.

This script initializes the retrieval and generation components of the system,
connecting a Neo4j database with language models (Ollama) to handle user
queries. The process follows these steps:

1. Load environment variables for database and LLM configuration.
2. Initialize the Neo4j database connection.
3. Initialize an Ollama-based LLM to act as a retriever (query generation).
4. Wrap the retriever in a Graph-based retriever that queries Neo4j.
5. Initialize another Ollama-based LLM to act as a generator (final response).
6. Combine the retriever and generator in a BasicGenerator pipeline.
7. Format the user prompt and generate the final response.
"""

from langchain_ollama.embeddings import OllamaEmbeddings
from neo4j import Driver, GraphDatabase, Result
from graphygie.llm.tools import tool
from graphygie.retrieval import Graph
from graphygie.retrieval.database import Neo4j, Database
from graphygie.llm import LLM, Ollama, Message
from graphygie.generation import BasicGenerator
import logging
from util import (
    read_to_string,
    unwrap,
    strip_code_fences,
    strip_after_double_newline,
    user_prompt,
    generator_system_prompt,
    compose,
)

from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = unwrap(os.getenv("NEO4J_URI"))
NEO4J_USERNAME = unwrap(os.getenv("NEO4J_USERNAME"))
NEO4J_PASSWORD = unwrap(os.getenv("NEO4J_PASSWORD"))
NEO4J_DATABASE = unwrap(os.getenv("NEO4J_DATABASE"))
NEO4J_EMBED_INDEX = unwrap(os.getenv("NEO4J_EMBED_INDEX"))

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))
MODEL = unwrap(os.getenv("MODEL"))
EMBEDDING_MODEL = unwrap(os.getenv("EMBEDDING_MODEL"))

CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))


@tool
def get_k_closest_CUI(query_text: str, k: int = 1) -> list[str]:
    """
    Retrieves the 'elementId' of the k CUI semantically closest to the 'query_text' using vector embeddings

    :param str query_text: The name or text content to search for
    :param int k: The number of nearest neighbors to return
    """
    driver: Driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    embedder: OllamaEmbeddings = OllamaEmbeddings(
        base_url=OLLAMA_URI, model=EMBEDDING_MODEL
    )
    driver.verify_connectivity()
    with driver.session(database=NEO4J_DATABASE) as session:
        results: Result = session.run(
            """
            CALL db.index.vector.queryNodes($index_name, $k, $search_vector)
            YIELD node, score
            RETURN elementId(node) AS elementId 
            """,
            index_name=NEO4J_EMBED_INDEX,
            k=k,
            search_vector=embedder.embed_query(query_text),
        )
        return [record["elementId"] for record in results]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="{levelname}:{name}:\n{message}", style="{"
    )

    current_dir: str = os.path.dirname(os.path.abspath(__file__))

    # Initialize the Neo4j database with credentials and connection URI from
    # environment variables
    database: Database = Neo4j(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        excluded_properties=["embedding"],
    )

    # Initialize the Ollama language model
    # - Connects to Ollama API using the host from environment variables
    # - Starts with a system prompt loaded from a file
    # - Applies a custom cleaner function to trim the model's response
    retrieval_llm: LLM = Ollama(
        host=OLLAMA_URI,
        model=MODEL,
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(current_dir, "resources/prompt/retrieval_system.md")
                ),
            )
        ],
        tools=[get_k_closest_CUI],
        cleaner=compose(strip_code_fences, strip_after_double_newline),
    )

    # Create a graph-based retriever using the LLM and database
    retrieval: LLM = Graph(llm=retrieval_llm, database=database)

    # Initialize the Ollama language model
    # - Connects to Ollama API using the host from environment variables
    generator_llm: LLM = Ollama(
        host=unwrap(os.getenv("OLLAMA_URI")),
        model=MODEL,
    )

    # Load the user prompt template from a file
    base: str = read_to_string(os.path.join(current_dir, "resources/prompt/user.md"))

    # RAG Orchestrator
    # - Provides information retrieval
    # - Provides a generation LLM
    # - Starts with a system prompt loaded from a file
    # - Applies a custom maker function to generate final system prompt
    generator: LLM = BasicGenerator(
        retriever=retrieval,
        generator=generator_llm,
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(current_dir, "resources/prompt/generator_system.md")
                ),
            )
        ],
        maker=generator_system_prompt,
    )

    # Launch of the RAG pipeline
    result: str = generator.chat(
        chat=[
            Message(
                role="user",
                content=user_prompt(
                    base,
                    intent="Information request",
                    request="What is the link between Crohn's disease and ankylosing spondylitis?",
                ),
            )
        ]
    )

    print("Result:\n", result)


if __name__ == "__main__":
    main()
