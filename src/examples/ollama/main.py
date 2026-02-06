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

from graphygie.retrieval import Graph
from graphygie.retrieval.database import Neo4j, Database
from graphygie.chat import Chattable, Message
from graphygie.llm import Ollama
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

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))


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
    )

    # Initialize the Ollama language model
    # - Connects to Ollama API using the host from environment variables
    # - Uses the "mistral:7b" model
    # - Starts with a system prompt loaded from a file
    # - Applies a custom cleaner function to trim the model's response
    retrieval_llm: Chattable = Ollama(
        host=OLLAMA_URI,
        model="mistral:7b",
        chat=[
            Message(
                role="system",
                content=read_to_string(
                    os.path.join(current_dir, "resources/prompt/retrieval_system.md")
                ),
            )
        ],
        cleaner=compose(strip_code_fences, strip_after_double_newline),
    )

    # Create a graph-based retriever using the LLM and database
    retrieval: Chattable = Graph(query_gen=retrieval_llm, database=database)

    # Initialize the Ollama language model
    # - Connects to Ollama API using the host from environment variables
    # - Uses the "mistral:7b" model
    generator_llm: Chattable = Ollama(
        host=OLLAMA_URI,
        model="mistral:7b",
    )

    # Load the user prompt template from a file
    base: str = read_to_string(os.path.join(current_dir, "resources/prompt/user.md"))

    # RAG Orchestrator
    # - Provides information retrieval
    # - Provides a generation LLM
    # - Starts with a system prompt loaded from a file
    # - Applies a custom maker function to generate final system prompt
    generator: Chattable = BasicGenerator(
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
                    request="What are the main cognitive and behavioral changes associated with Frontal Lobe Syndrome?",
                ),
            )
        ]
    )

    print("Result:\n", result)


if __name__ == "__main__":
    main()
