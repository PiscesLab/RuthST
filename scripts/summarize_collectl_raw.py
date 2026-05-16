import argparse, gzip, re
from pathlib import Path
import pandas as pd

CLK_TCK = 100.0

def parse_file(path):
    samples = []
    cur = None

    with gzip.open(path, "rt", errors="ignore") as f:
        for line in f:
            line = line.strip()

            m = re.match(r">>>\s+([\d.]+)\s+<<<", line)
            if m:
                if cur:
                    samples.append(cur)
                cur = {"ts": float(m.group(1))}
                continue

            if cur is None:
                continue

            parts = line.split()

            if len(parts) >= 11 and parts[0] == "cpu":
                vals = list(map(int, parts[1:11]))
                cur["cpu_total"] = sum(vals)
                cur["cpu_idle"] = vals[3]
                cur["cpu_iowait"] = vals[4]

            elif len(parts) >= 6 and parts[0] == "disk":
                # collectl raw disk line includes cumulative sectors/read-write counters.
                # These fields are kernel-style diskstats counters.
                try:
                    cur["disk_read_sectors"] = int(parts[5])
                    cur["disk_write_sectors"] = int(parts[9])
                except Exception:
                    pass

            elif line.startswith("MemTotal:"):
                cur["mem_total_kb"] = int(parts[1])
            elif line.startswith("MemFree:"):
                cur["mem_free_kb"] = int(parts[1])
            elif line.startswith("Buffers:"):
                cur["buffers_kb"] = int(parts[1])
            elif line.startswith("Cached:"):
                cur["cached_kb"] = int(parts[1])

    if cur:
        samples.append(cur)

    rows = []
    for a, b in zip(samples, samples[1:]):
        dt = b["ts"] - a["ts"]
        if dt <= 0:
            continue

        rec = {"ts": b["ts"], "dt": dt}

        if "cpu_total" in a and "cpu_total" in b:
            d_total = b["cpu_total"] - a["cpu_total"]
            d_idle = b["cpu_idle"] - a["cpu_idle"]
            d_iowait = b["cpu_iowait"] - a["cpu_iowait"]

            if d_total > 0:
                rec["cpu_busy_pct"] = 100.0 * (d_total - d_idle) / d_total
                rec["cpu_iowait_pct"] = 100.0 * d_iowait / d_total

        if "disk_read_sectors" in a and "disk_read_sectors" in b:
            rec["disk_read_mb_s"] = ((b["disk_read_sectors"] - a["disk_read_sectors"]) * 512.0 / 1024 / 1024) / dt

        if "disk_write_sectors" in a and "disk_write_sectors" in b:
            rec["disk_write_mb_s"] = ((b["disk_write_sectors"] - a["disk_write_sectors"]) * 512.0 / 1024 / 1024) / dt

        if "mem_total_kb" in b and "mem_free_kb" in b:
            buffers = b.get("buffers_kb", 0)
            cached = b.get("cached_kb", 0)
            rec["mem_used_gb"] = (b["mem_total_kb"] - b["mem_free_kb"] - buffers - cached) / 1024 / 1024

        rows.append(rec)

    return pd.DataFrame(rows)

def summarize_one(path):
    df = parse_file(path)
    rec = {"file": path.name, "samples": len(df)}

    for col in ["cpu_busy_pct", "cpu_iowait_pct", "disk_read_mb_s", "disk_write_mb_s", "mem_used_gb"]:
        if col in df:
            rec[f"avg_{col}"] = df[col].mean()
            rec[f"max_{col}"] = df[col].max()

    return rec

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collectl-dir", default="logs/collectl")
    parser.add_argument("--output", default="results/worker_sweep_2/collectl_raw_summary.csv")
    args = parser.parse_args()

    records = []
    for p in sorted(Path(args.collectl_dir).glob("*.raw.gz")):
        records.append(summarize_one(p))

    out = pd.DataFrame(records)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(out)
    print(f"[Saved] {args.output}")

if __name__ == "__main__":
    main()
