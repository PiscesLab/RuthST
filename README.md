# RuthST

RuthST is a cloud-oriented preprocessing and workflow orchestration framework that bridges large-scale RUTH traffic simulation outputs with downstream spatio-temporal (ST) intelligence pipelines. The project utilizes Parsl for parallel trajectory transformation and investigates the workflow behaviors, scalability limitations, and resource bottlenecks that emerge during large-scale ST dataset construction.

Rather than focusing solely on traffic simulation itself, RuthST studies how cloud-oriented preprocessing workflows transform large floating car data (FCD) collections into ML-ready ST datasets for downstream forecasting and analytics.

---

# 🌟 Key Features

## Cloud-Oriented Workflow Orchestration

- Parsl-based parallel preprocessing pipeline
- Chunk-level distributed task execution
- Configurable worker counts and chunk sizes
- Workflow instrumentation and timing analysis

## Large-Scale ST Dataset Construction

- Dual-metric extraction:
  - Average Speed (mph)
  - Traffic Flow (Unique Vehicle Count)
- Temporal tensor generation for ST forecasting
- Flexible temporal sampling intervals
- Peak-period dataset segmentation

## Workflow Characterization

- End-to-end workflow latency analysis
- Worker scalability evaluation
- Chunk-size sensitivity analysis
- Aggregation overhead characterization
- Resource utilization monitoring

## Resource Monitoring

- collectl-based runtime monitoring
- CPU utilization analysis
- Memory usage characterization
- Workflow bottleneck analysis

---

# 📂 Project Structure

```text
RuthST/
├── data/
│   ├── raw/               # Raw RUTH H5 files (Git ignored)
│   ├── processed/         # Intermediate processed H5 outputs
│   └── ruth/              # Final ST datasets for model training
│
├── dataprep/
│   ├── config.py          # Global constants and workflow settings
│   ├── parsl_config.py    # Parsl execution environment setup
│   ├── parsl_worker.py    # Parallel chunk processing logic
│   ├── aggregator.py      # Task orchestration and merging
│   └── graph_meta.py      # Graph metadata generation
│
├── scripts/
│   ├── run_conversion_eval.py
│   ├── parse_runtime_logs.py
│   ├── parse_collectl_logs.py
│   └── ...
│
├── notebooks/             # Visualization and workflow analysis
├── experiments/           # ST model training experiments
├── src/                   # ML essentials
├── logs/
├── results/
├── figures/
├── main.py
└── README.md
```

---

# 🚀 Quick Start

## 1. Prerequisites

Install dependencies:

```bash
pip install pandas numpy tables parsl matplotlib seaborn networkx
```

Additional details are available in `requirements.txt`.

---

## 2. Data Setup

### Raw Data

Place RUTH-generated HDF5 trajectory files under:

```text
data/raw/
```

### Metadata

The workflow requires road network metadata containing:

- OSM road segment information
- Road category labels
- Edge-to-index mappings

### Spatial Mapping

Road segments are mapped into fixed ST matrix indices using:

```text
edge_to_idx
```

for downstream tensor generation.

---

## 3. Run the Workflow

Example preprocessing execution:

```bash
python scripts/run_conversion_eval.py \
  --city cbr \
  --portion 2pc \
  --workers 16 \
  --chunk-size 16000000 \
  --skip-adj
```

The workflow will:

1. Initialize the Parsl execution environment
2. Read raw HDF5 trajectory data in chunks
3. Perform parallel dual-metric aggregation
4. Generate speed and flow matrices
5. Filter road categories
6. Split datasets by temporal windows
7. Save processed outputs into `data/processed/`

---

# 📊 Data Processing Logic

## Metric Conversion

### Speed

Raw vehicle speed is stored in meters-per-second (`speed_mps`).

The workflow computes:

```text
Mean Speed → Miles Per Hour (mph)
```

using:

```text
2.23694
```

as the conversion factor.

### Flow

Traffic flow is defined as:

```text
Unique Vehicle Count per Road Segment
```

within each temporal interval.

### Temporal Filling

Missing intervals are filled with zeros to maintain dense and continuous ST tensors.

---

# Spatial Filtering

To align with LargeST-style ST forecasting workflows, the pipeline filters the original road network and retains major infrastructure categories:

- motorway
- trunk
- primary
- secondary

This reduces the original 29k+ road segments into compact ST forecasting tensors.

---

# ⚡ Workflow Optimization

## Vectorized ID Mapping

The preprocessing pipeline avoids row-wise `.apply()` operations and instead uses vectorized tuple-based dictionary lookups for trajectory-to-road mapping.

This significantly reduces mapping overhead for large-scale FCD datasets.

---

## Memory-Efficient Chunking

Large trajectory files may contain hundreds of millions of records.

To reduce memory pressure, the workflow uses:

```python
pd.read_hdf(..., start=..., stop=...)
```

for chunk-level processing.

This allows large-scale preprocessing on moderate-memory cloud nodes.

---

## Parallel Execution with Parsl

The preprocessing workload is distributed across multiple CPU workers using Parsl.

Each worker independently processes a chunk of the trajectory dataset, enabling parallel ST tensor generation and aggregation.

---

# 📈 Workflow Characterization

The current implementation includes workflow characterization experiments focusing on:

- Increasing workload scales
- Worker scalability behavior
- Aggregation bottlenecks
- Memory utilization trends
- Chunk-size sensitivity

Preliminary observations show:

- Chunk-level parallelism substantially reduces preprocessing latency
- Workflow scalability gradually saturates at higher concurrency levels
- CPU utilization remains moderate under increasing worker counts
- Memory consumption increases substantially with concurrency
- Centralized aggregation becomes a dominant workflow bottleneck

These findings motivate future exploration of:

- Distributed aggregation
- Streaming-based preprocessing
- Multi-node orchestration
- Cloud-native workflow execution

---

# 🌍 Experimental Datasets

Current evaluations include:

- Ostrava Morning
- Ostrava Evening
- Central Bohemia Region (CBR)

The evaluated workloads range from approximately:

```text
1M → 446M trajectory records
```

---

# 📊 Runtime Monitoring

## collectl Monitoring

Example:

```bash
collectl -scmd -i 1 -f logs/cbr_2pc_w16
```

## Runtime Log Parsing

```bash
python scripts/parse_runtime_logs.py \
  --log-dir logs \
  --output results/runtime_summary.csv
```

## collectl Log Parsing

```bash
python scripts/parse_collectl_logs.py \
  --log-dir logs \
  --output results/collectl_summary.csv
```

---

# 🔮 Future Directions

Planned future extensions include:

- Multi-node workflow orchestration
- Distributed aggregation mechanisms
- Streaming ST preprocessing
- Ray/Dask-based distributed execution
- Cloud-native deployment pipelines
- Integration with LEXIS cloud/HPC orchestration environments

---

# Citation

Citation information will be updated after publication.

---

# Acknowledgment

This project builds upon the RUTH traffic simulation ecosystem and investigates cloud-oriented workflow orchestration for large-scale ST intelligence pipelines.
