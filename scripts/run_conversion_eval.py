# scripts/run_conversion_eval.py

import os, sys, time, argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, REPO_ROOT)
os.environ["PYTHONPATH"] = REPO_ROOT + ":" + os.environ.get("PYTHONPATH", "")

from dataprep.graph_logic import generate_graph_metadata, generate_adjacency_matrix
from dataprep.aggregator import run_h5_conversion

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portion", type=str, default="100pc")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--city", type=str, default="ostrava")
    parser.add_argument("--skip-adj", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=2000000)
    args = parser.parse_args()

    total_start = time.time()
    print(f"[Eval] portion={args.portion}")

    graph_start = time.time()
    G, edge_to_idx, df_meta = generate_graph_metadata(city=args.city)
    if args.skip_adj:
        print("[Eval] skip adjacency matrix generation")
    else:
        generate_adjacency_matrix(G, edge_to_idx, df_meta, city=args.city)
    #generate_adjacency_matrix(G, edge_to_idx, df_meta, city=args.city)
    print(f"[Timing] graph_stage_sec={time.time() - graph_start:.2f}")

    conversion_start = time.time()
    #run_h5_conversion(args.portion, edge_to_idx, df_meta)
    run_h5_conversion(args.portion, edge_to_idx, df_meta, workers=args.workers, city=args.city, chunk_size=args.chunk_size)
    print(f"[Timing] conversion_stage_sec={time.time() - conversion_start:.2f}")

    print(f"[Timing] total_sec={time.time() - total_start:.2f}")

if __name__ == "__main__":
    main()
