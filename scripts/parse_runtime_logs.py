import re, os
import argparse
from pathlib import Path
import pandas as pd

def parse_log(path):
    txt = Path(path).read_text(errors="ignore")

    #rec = {"file": Path(path).name}
    #m = re.search(r"w(\d+)_r(\d+)", rec["file"])
    #if m:
    #    rec["workers"] = int(m.group(1))
    #    rec["repeat"] = int(m.group(2))

    name = Path(path).name
    rec = {"file": name}

    m = re.search(r"^(ostrava|cbr)_", name)
    if m:
        rec["city"] = m.group(1)

    m = re.search(r"_(\d+pc)_", name)
    if m:
        rec["portion"] = m.group(1)

    m = re.search(r"_w(\d+)", name)
    if m:
        rec["workers"] = int(m.group(1))

    m = re.search(r"_chunk(\d+)", name)
    if m:
        rec["chunk_size"] = int(m.group(1))

    m = re.search(r"_r(\d+)", name)
    rec["repeat"] = int(m.group(1)) if m else 1

    patterns = {
        "conversion_sec": r"\[Timing\] conversion_stage_sec=([\d.]+)",
        "total_sec": r"\[Timing\] total_sec=([\d.]+)",
        "cpu_percent": r"Percent of CPU this job got:\s+(\d+)%",
        "rss_kb": r"Maximum resident set size \(kbytes\):\s+(\d+)",
        "wall_time": r"Elapsed \(wall clock\) time.*:\s+([\d:.\-]+)"
    }

    for k, p in patterns.items():
        mm = re.search(p, txt)
        if mm:
            rec[k] = mm.group(1)

    if "rss_kb" in rec:
        rec["rss_gb"] = float(rec["rss_kb"]) / 1024 / 1024

    return rec

#def parse_wall_to_sec(s):
#    if ":" not in s:
#        return float(s)

#    parts = s.split(":")
#    parts = [float(x) for x in parts]

#    if len(parts) == 2:
#        return parts[0] * 60 + parts[1]

#    if len(parts) == 3:
#        return parts[0] * 3600 + parts[1] * 60 + parts[2]

#    return None
def parse_wall_to_sec(s):
    if pd.isna(s):
        return None

    s = str(s).strip()

    if ":" not in s:
        return float(s)

    parts = [float(x) for x in s.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--output", default="results/worker_sweep_2/runtime_summary.csv")
    args = parser.parse_args()

    rows = []

    for p in sorted(Path(args.log_dir).glob("*.log")):
    #for p in sorted(Path(args.log_dir).glob("ostrava_0pc_w*_r*.log")):
        if "master" in p.name:
            continue
        rows.append(parse_log(p))

    df = pd.DataFrame(rows)

    numeric_cols = ["conversion_sec", "total_sec", "cpu_percent", "rss_gb"]

    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "wall_time" in df.columns:
        df["wall_sec"] = df["wall_time"].apply(parse_wall_to_sec)

    #df = df.sort_values(["workers", "repeat"])
    sort_cols = [c for c in ["city", "portion", "workers", "chunk_size", "repeat"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print(df)

    print("\n=== Aggregated ===")
    agg = df.groupby("workers").agg({
        "conversion_sec": ["mean", "std"],
        "total_sec": ["mean", "std"],
        "wall_sec": ["mean", "std"],
        "rss_gb": ["mean", "std"],
    })

    print(agg)

    #agg.to_csv("results/worker_sweep_2/runtime_aggregated.csv")
    os.makedirs("results/cbr_workload_scaling", exist_ok=True)
    agg.to_csv("results/cbr_workload_scaling/runtime_aggregated.csv")
    
    print(f"\n[Saved] {args.output}")
    #print("[Saved] results/worker_sweep_2/runtime_aggregated.csv")

if __name__ == "__main__":
    main()
