# Med-KAG: Knowledge Augmented Generation for Medical Decision Support

Med-KAG is an AI assistant architecture designed to improve the reliability of clinical decision support by integrating a structured Knowledge Graph (KG) into the Retrieval-Augmented Generation (RAG) paradigm. The system grounds LLM responses in the UMLS Metathesaurus to reduce factual hallucinations and provide traceable, verifiable reasoning.

> **Research context:** This repository accompanies the paper *"Med-KAG, une approche de génération augmentée par connaissances médicales : Analyse des performances et limites de la récupération par embedding"* (Haddag, Medeiros, Soualmia — LITIS, Univ Rouen Normandie, 2025), evaluating Med-KAG on the PubMedQA benchmark.

---

## Architecture

Med-KAG is built on top of **Graphygie**, a Python library included in this repository that provides a modular interface for building GraphRAG pipelines. The system follows a linear pipeline (Native RAG), designed to evolve toward a Modular RAG framework supporting auto-correction and hybrid retrieval.

The pipeline works as follows:

1. A user query is embedded using an embedding model (EmbeddingGemma by default).
2. The embedding is used to query a Neo4j knowledge graph built from the UMLS Metathesaurus.
3. A sub-graph of relevant medical concepts and their relationships is extracted.
4. The sub-graph context (as triplets or natural-language summary) is passed to a generator LLM (Qwen3).
5. An optional cleaner LLM normalizes the output format.

Two retrieval strategies are supported:

- **Vector-based retrieval** — embedding similarity search to extract a semantic sub-graph (current implementation).
- **Text-to-Cypher retrieval** — LLM-generated Cypher queries for targeted graph traversal (primary future direction).

---

## Benchmark Results

Evaluation was conducted on **PubMedQA** (500 questions, yes/no/maybe format). Results show that the current embedding-based retrieval degrades accuracy compared to the native baseline, due to noisy sub-graphs in highly connected regions of the UMLS graph.

| Model | Accuracy | Time (s) |
|---|---|---|
| Native (Qwen3-1.7B) | 49.00% (245/500) | 15.04 |
| Native (Qwen3-4B) | 51.60% (258/500) | 108.33 |
| RAG (Qwen3-1.7B) | 39.60% (198/500) | 76.21 |
| RAG (Qwen3-4B) | 37.40% (187/500) | 325.18 |
| RAG-Cleaner (Qwen3-1.7B) | 46.00% (230/500) | 94.23 |
| RAG-Sum-Cleaner (Qwen3-1.7B) | 37.00% (185/500) | 178.27 |

Average sub-graph size for RAG retrievals: 102.55 nodes / 228.74 edges (median: 83 / 185).

The performance gap is explained by the UMLS graph topology: in highly connected zones, vector search returns large, noisy sub-graphs that dilute the relevant context. These results do not invalidate the KAG approach; they identify the retrieval module as the bottleneck to address.

---

## Project Structure

```
src/
  graphygie/          # Core library: chat, embedding, LLM wrappers, Neo4j retrieval
    chat/             # Chattable interface and Message types
    embedding/        # Embedder interface, Ollama embedding
    generation/       # BasicGenerator pipeline
    llm/              # Ollama and OpenAI LLM adapters, tool definitions
    retrieval/        # Graph retriever, Neo4j database, Cypher/vector query,
                      # triplet and summary converters
  benchmark/          # Benchmark harness for PubMedQA evaluation
    programs/         # One script per experimental configuration
    resources/prompt/ # System prompts for each pipeline stage
    results/          # Per-question JSON result files
  examples/           # Runnable examples (Ollama, OpenAI, agent, no-graphygie)
  util/               # Shared utilities: prompt loading, composition, cleaning
```

---

## Getting Started

### Prerequisites

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) package manager
- A running Neo4j instance loaded with the UMLS graph dump ([see](https://zenodo.org/records/10911980/files/BioPropaPhenKG.dump))
- An Ollama or OpenAI-compatible endpoint

### Installation

```bash
git clone https://github.com/c2fc2f/Med-KAG.git
cd Med-KAG
uv sync --extra examples
```

This creates a virtual environment and installs all dependencies from `pyproject.toml`.

### Configuration

Copy the relevant `.env_example` file and fill in your credentials:

```bash
cp src/examples/agent/.env_example src/examples/agent/.env
```

Required environment variables:

```
MODEL = "qwen3:1.7b"

NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""
NEO4J_DATABASE = "neo4j"
NEO4J_EMBED_INDEX = "CUI_EMBEDDINGS"

OLLAMA_URI = "https://example.com"
EMBEDDING_MODEL = "embeddinggemma:latest"

OPENAI_URI=https://openrouter.ai/api/v1   # or any OpenAI-compatible endpoint
OPENAI_TOKEN = "<token>"
```

### Running an Example

**With Ollama:**
```bash
uv run graphygie-ollama
```

**With OpenAI-compatible API:**
```bash
uv run graphygie-openai
```

**Agentic pipeline (Text-to-Cypher):**
```bash
uv run graphygie-agent
```

**Without Graphygie (direct Neo4j embedding):**
```bash
uv run no-graphygie-neo4j
uv run no-graphygie-neo4j-embedding
```

---

## Running the Benchmark

```bash
cp src/benchmark/.env_example src/benchmark/.env
# Fill in your environment variables

uv sync --extra benchmark

uv run benchmark --help
```

Individual benchmark configurations can be run directly:

```bash
uv run benchmark rag-kg-summary-vector-cleaner-llm-qwen3-1-7b
```

Results are written as JSON files to `src/benchmark/results/pubmedqa/`, one file per question.

Analysis utilities are available in `src/benchmark/programs/stats.py` and `src/benchmark/programs/find-diff.py`.

---

## Experimental Configurations

The benchmark tests four pipeline variants:

| Configuration | Description |
|---|---|
| **Native** | Qwen3 with no retrieval augmentation (baseline) |
| **RAG** | Vector embedding retrieval from UMLS, raw triplets injected as context |
| **RAG-Cleaner** | RAG with a post-processing LLM to normalize the output format |
| **RAG-Sum-Cleaner** | RAG with an intermediate summarizer that verbalizes triplets into natural language, followed by the cleaner |

---

## Roadmap

The primary bottleneck identified is the embedding-based retrieval, which extracts large sub-graphs in densely connected UMLS regions. Two improvement axes are planned:

**Semantic reranking:** Post-retrieval filtering or pruning to reduce sub-graph size and noise before passing context to the generator.

**Text-to-Cypher transition:** LLM-generated Cypher queries allow targeted traversal of specific graph paths, avoiding the "suffers from graph connectivity" problem of vector search. This is the preferred long-term direction and is already scaffolded in `src/examples/agent/`.

Future validation will target real clinical data from health data warehouses.

---

## License

This project is licensed under the **GNU General Public License v3.0**.

UMLS data and graph dumps are the property of the U.S. National Library of Medicine (NLM). Usage must comply with their [licensing terms](https://www.nlm.nih.gov/databases/umls.html).
