from neo4j import GraphDatabase
from langchain_ollama import OllamaEmbeddings
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv
from tqdm import tqdm
from util import unwrap
import time


load_dotenv()

# Configuration
NUM_THREADS = 50
BATCH_SIZE = 100

NEO4J_URI = unwrap(os.getenv("NEO4J_URI"))
NEO4J_USERNAME = unwrap(os.getenv("NEO4J_USERNAME"))
NEO4J_PASSWORD = unwrap(os.getenv("NEO4J_PASSWORD"))
NEO4J_DATABASE = unwrap(os.getenv("NEO4J_DATABASE"))

OLLAMA_URI = unwrap(os.getenv("OLLAMA_URI"))
EMBEDDING_MODEL = unwrap(os.getenv("EMBEDDING_MODEL"))

# Lock for shared statistics
stats_lock = Lock()
stats = {"processed": 0, "errors": 0, "start_time": time.time()}


def create_embedder():
    """ "Creates an embedder for each thread"""
    return OllamaEmbeddings(base_url=OLLAMA_URI, model=EMBEDDING_MODEL)


def create_driver():
    """Creates a Neo4j driver for each thread"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def fetch_cui_batch(driver, offset, limit):
    """Retrieves a batch of CUI nodes without embedding"""
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            """
            MATCH (c:CUI)
            WHERE c.embedding IS NULL
            RETURN c.id AS id, c.name AS name
            SKIP $offset
            LIMIT $limit
        """,
            offset=offset,
            limit=limit,
        )
        return [{"id": r["id"], "name": r["name"]} for r in result]


def process_cui_batch(batch, thread_id):
    """Processes a batch of CUIs in a thread"""
    driver = create_driver()
    embedder = create_embedder()

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            for cui in batch:
                try:
                    # Generate embedding
                    embedding = embedder.embed_query(cui["name"])

                    # Update the node
                    session.run(
                        """
                        MATCH (c:CUI {id: $id})
                        SET c.embedding = $embedding
                    """,
                        id=cui["id"],
                        embedding=embedding,
                    )

                    # Statistics update
                    with stats_lock:
                        stats["processed"] += 1
                        if stats["processed"] % 100 == 0:
                            elapsed = time.time() - stats["start_time"]
                            rate = stats["processed"] / elapsed
                            print(
                                f"✓ Thread {thread_id}: {stats['processed']} CUI processed "
                                f"({rate:.2f} CUI/s, Errors: {stats['errors']})"
                            )

                except Exception as e:
                    with stats_lock:
                        stats["errors"] += 1
                    print(f"✗ Thread {thread_id}: Error of {cui['id']}: {e}")

    finally:
        driver.close()

    return len(batch)


def count_cui_without_embeddings(driver):
    """Count the number of CUI without embedding"""
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run("""
            MATCH (c:CUI)
            WHERE c.embedding IS NULL
            RETURN count(c) AS count
        """)
        return result.single()["count"]


def main():
    print("🚀 Starting parallel embedding generation...")
    print(f"⚙️ Configuration: {NUM_THREADS} threads, batch size: {BATCH_SIZE}")

    # Initial connection to count
    driver = create_driver()
    total_cui = count_cui_without_embeddings(driver)
    print(f"📊 Total CUI without embedding: {total_cui:,}")

    if total_cui == 0:
        print("✅ All CUI already have embeddings!")
        driver.close()
        return

    # Calculate the number of batches
    num_batches = (total_cui + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 Number of batches: {num_batches}")

    # Retrieve all batches first
    print("📥 CUI recovery...")
    all_batches = []
    for i in tqdm(range(num_batches), desc="Recuperation of CUI"):
        offset = i * BATCH_SIZE
        batch = fetch_cui_batch(driver, offset, BATCH_SIZE)
        if batch:
            all_batches.append(batch)

    driver.close()
    print(f"✓ {len(all_batches)} recuperated batches")

    # Process in parallel
    print(f"\n⚡ Processing with {NUM_THREADS} threads...\n")

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for idx, batch in enumerate(all_batches):
            thread_id = idx % NUM_THREADS
            future = executor.submit(process_cui_batch, batch, thread_id)
            futures.append(future)

        # Wait for all threads to finish
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Erreur dans un thread: {e}")

    # Final statistics
    elapsed = time.time() - stats["start_time"]
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("📊 Statistics:")
    print(f"   - CUI processed: {stats['processed']:,}")
    print(f"   - Errors: {stats['errors']}")
    print(f"   - Total time: {elapsed:.2f}s")
    print(f"   - Average speed: {stats['processed'] / elapsed:.2f} CUI/s")
    print("=" * 60)


if __name__ == "__main__":
    main()
