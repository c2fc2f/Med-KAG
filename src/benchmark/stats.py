import json
import os
from pathlib import Path
from statistics import mean, median
from typing import Any


CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR: str = os.path.join(CURRENT_DIR, "results")
BENCHMARK_FILE: str = os.path.join(CURRENT_DIR, "benchmark.json")

def load_benchmark(benchmark_path: str) -> Any:
    """Load the benchmark.json file"""
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_results(results_dir: str, benchmark_path: str):
    """Analyze native and RAG results"""
    
    # Load benchmark
    benchmark: Any = load_benchmark(benchmark_path)
    
    # Statistics
    native_correct: dict[str, int] = dict()
    native_total: dict[str, int] = dict()
    rag_correct: dict[str, int] = dict()
    rag_total: dict[str, int] = dict()

    # For RAG metrics
    rag_errors: dict[str, list[int]] = dict()
    rag_nodes: dict[str, list[int]] = dict()
    rag_edges: dict[str, list[int]] = dict()
    
    # Browse all datasets
    results_path = Path(results_dir)
    
    for dataset_dir in results_path.iterdir():
        if not dataset_dir.is_dir():
            continue
            
        dataset_name: str = dataset_dir.name
        
        if dataset_name not in benchmark:
            print(f"⚠️  Dataset '{dataset_name}' not found in benchmark.json")
            continue

        native_correct[dataset_name] = 0
        native_total[dataset_name] = 0
        rag_correct[dataset_name] = 0
        rag_total[dataset_name] = 0

        rag_errors[dataset_name] = list()
        rag_nodes[dataset_name] = list()
        rag_edges[dataset_name] = list()

        
        # Browse result files
        for result_file in dataset_dir.glob("*.json"):
            filename: str = result_file.name
            
            # Identify type (native or rag) and question
            if filename.startswith("native_"):
                question_name: str = filename[7:-5]  # Remove "native_" and ".json"
                result_type: str = "native"
            elif filename.startswith("rag_"):
                question_name: str = filename[4:-5]  # Remove "rag_" and ".json"
                result_type: str = "rag"
            else:
                continue
            
            # Check if question exists in benchmark
            if question_name not in benchmark[dataset_name]:
                print(f"⚠️  Question '{question_name}' not found in benchmark[{dataset_name}]")
                continue
            
            # Load result
            with open(result_file, 'r', encoding='utf-8') as f:
                result: Any = json.load(f)
            
            # Get correct answer
            correct_answer: str = benchmark[dataset_name][question_name]["answer"]
            user_response: str = result.get("response")
            
            # Count results
            if result_type == "native":
                native_total[dataset_name] += 1
                if user_response == correct_answer:
                    native_correct[dataset_name] += 1
            else:  # rag
                rag_total[dataset_name] += 1
                if user_response == correct_answer:
                    rag_correct[dataset_name] += 1
                
                # Collect RAG metrics
                rag_errors[dataset_name].append(result.get("error", 0))
                rag_nodes[dataset_name].append(result.get("nodes", 0))
                rag_edges[dataset_name].append(result.get("edges", 0))

    # Display results
    print("=" * 60)
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    print()

    for name in native_correct.keys():

        print("=" * 45)
        print(f"ANALYSIS RESULTS FOR {name}")
        print("=" * 45)
        print()
    
        # Calculate accuracy rates
        native_accuracy: float = (native_correct[name] / native_total[name] * 100) if native_total[name] > 0 else 0
        rag_accuracy: float = (rag_correct[name] / rag_total[name] * 100) if rag_total[name] > 0 else 0
     
        print("🔵 NATIVE")
        print(f"  ✓ Correct answers: {native_correct[name]}/{native_total[name]}")
        print(f"  📈 Accuracy rate: {native_accuracy:.2f}%")
        print()
    
        print("🟢 RAG")
        print(f"  ✓ Correct answers: {rag_correct[name]}/{rag_total[name]}")
        print(f"  📈 Accuracy rate: {rag_accuracy:.2f}%")
        print()
    
        if rag_errors[name]:
            print("📉 RAG METRICS")
            print(f"  Errors     - Mean: {mean(rag_errors[name]):.2f} | Median: {median(rag_errors[name]):.2f}")
            print(f"  Nodes      - Mean: {mean(rag_nodes[name]):.2f} | Median: {median(rag_nodes[name]):.2f}")
            print(f"  Edges      - Mean: {mean(rag_edges[name]):.2f} | Median: {median(rag_edges[name]):.2f}")
        print()
    
        print("=" * 45)
        print()

    print("=" * 45)
    print("ANALYSIS RESULTS TOTAL")
    print("=" * 45)
    print()

    # Calculate accuracy rates
    native_accuracy: float = (sum(native_correct.values()) / sum(native_total.values()) * 100) if sum(native_total.values()) > 0 else 0
    rag_accuracy: float = (sum(rag_correct.values()) / sum(rag_total.values()) * 100) if sum(rag_total.values()) > 0 else 0

    print("🔵 NATIVE")
    print(f"  ✓ Correct answers: {sum(native_correct.values())}/{sum(native_total.values())}")
    print(f"  📈 Accuracy rate: {native_accuracy:.2f}%")
    print()

    print("🟢 RAG")
    print(f"  ✓ Correct answers: {sum(rag_correct.values())}/{sum(rag_total.values())}")
    print(f"  📈 Accuracy rate: {rag_accuracy:.2f}%")
    print()

    if rag_errors:
        print("📉 RAG METRICS")
        print(f"  Errors     - Mean: {mean(sum(rag_errors.values(), [])):.2f} | Median: {median(sum(rag_errors.values(), [])):.2f}")
        print(f"  Nodes      - Mean: {mean(sum(rag_nodes.values(), [])):.2f} | Median: {median(sum(rag_nodes.values(), [])):.2f}")
        print(f"  Edges      - Mean: {mean(sum(rag_edges.values(), [])):.2f} | Median: {median(sum(rag_edges.values(), [])):.2f}")
    print()

    print("=" * 60)

def main() -> None:
    # Check if files exist
    if not os.path.exists(RESULTS_DIR):
        print(f"❌ Error: Directory '{RESULTS_DIR}' does not exist")
        exit(1)
    
    if not os.path.exists(BENCHMARK_FILE):
        print(f"❌ Error: File '{BENCHMARK_FILE}' does not exist")
        exit(1)
    
    # Run analysis
    analyze_results(RESULTS_DIR, BENCHMARK_FILE)

if __name__ == "__main__":
    main()
