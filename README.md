# Med-KAG: Knowledge Augmented Generation for Medical Decision Support

Med-KAG is an AI assistant architecture designed to enhance the reliability of clinical decision support. By extending the Retrieval-Augmented Generation (RAG) paradigm through the integration of a structured Knowledge Graph (KG), Med-KAG aims to reduce factual hallucinations and provide traceable reasoning for medical diagnosis.

## Overview

Unlike traditional RAG systems that rely on unstructured text, Med-KAG anchors the generation process in the **UMLS Metathesaurus**. This ensures that the model's responses are constrained by verified medical relationships between diseases, symptoms, and treatments.

### Key Features

* **Knowledge-Anchored Generation:** Replaces standard vector-based text retrieval with a structured Knowledge Graph (KG) derived from UMLS.
* **Traceable Reasoning:** Provides transparency by identifying and extracting relevant sub-graphs (concepts and relations) used to formulate a response.
* **LLM-Powered Retrieval:** Uses advanced models (such as Qwen3-235B-A22B) to generate Cypher queries for precise data extraction from Neo4j.
* **Modular Design:** Built to evolve from a linear pipeline into a Modular RAG framework, supporting future iterations like auto-correction and hybrid search.

## Preliminary Results

In evaluations using the **MedQA-US** dataset, the Med-KAG architecture demonstrated:

* **High Diagnostic Accuracy:** Achieved a precision of **91.28%**, comparable to the native Qwen3-235B-A22B baseline (91.67%).
* **Transparency:** Successfully identifies key entities (e.g., "flexor tendon") and their semantic neighborhoods to provide clinical context.
* **Identified Bottlenecks:** Analysis pinpointed LLM-based Cypher generation as a primary area for improvement, with a 22% syntax error rate in this preliminary iteration.

## Future Roadmap

Immediate development focuses on a **hybrid retriever** that combines semantic embedding-based search with graph traversal to improve the robustness of entity linking and overall clinical assistance.

---

## 🧰 Features

* Uses the UMLS Neo4j graph dump provided by the original GraphRAG publication.
* Provides a `setup.sh` script to download, import, and migrate the Neo4j database.
* Launches a local Neo4j instance using Docker Compose.
* Modular and type-annotated Python codebase.
* Interface-based architecture for flexibility and clarity.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/c2fc2f/Med-KAG.git
cd Med-KAG
```

### 2. Prepare the Neo4j Graph Database

Run the setup script (only once):

```bash
chmod +x setup.sh
./setup.sh
```

This will:

* Download the Neo4j dump file from [Zenodo](https://zenodo.org/records/10911980)
* Load it into the proper `data/` directory
* Run necessary migrations

> 🔧 The database is not turn-key out of the box — it must be set up manually using this script.

### 3. Launch the Neo4j Server

```bash
docker compose up -d neo4j
```

This will start a local Neo4j server accessible at `bolt://localhost:7687` with default credentials (`neo4j/<empty password>`).

### 4. Install Python Dependencies

```bash
uv sync --extra examples
```

> This will create a virtual environment and install all dependencies from `pyproject.toml`

### 5. Run the Application

```bash
uv run graphygie-openrouter
```

---

## 📄 License

This project is licensed under the GPLv3 License.
UMLS data and graph dumps are property of the U.S. National Library of Medicine (NLM). Usage must comply with their licensing terms.
