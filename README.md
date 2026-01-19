# RuthST
This project bridges the gap between RUTH simulation and LargeST benchmark using Parsl for high-performance data transformation.

## 🌟 Key Features

* **Parallel Acceleration**: Powered by the `Parsl` framework for high-speed multi-core processing of massive HDF5 files.
* **Dual-Metric Extraction**: Generates both **Average Speed (mph)** and **Traffic Flow (Unique Vehicle Count)** matrices in a single pass.
* **Flexible Sampling**: Supports customizable time intervals (e.g., `5s`, `1min`, `5min`, `15min`) via global configuration.
* **Peak Period Splitting**: Automatically extracts and segments data into **Morning Peak (05:00-08:00)** and **Evening Peak (14:00-17:00)** datasets.
* **Spatial Alignment**: Filters the 29k+ road segments to focus on core infrastructure (`motorway`, `trunk`, `primary`, `secondary`) based on metadata.

---

## 📂 Project Structure

```text
├── data/
│   ├── raw/               # Raw RUTH H5 files (Git ignored)
│   └── processed/         # Processed Speed/Flow H5 files (Git ignored)
├── src/
│   ├── config.py          # Global constants (intervals, paths, peak hours)
│   ├── parsl_config.py    # Parsl execution environment setup
│   ├── parsl_worker.py    # Parallel app logic (Vectorized Mapping & Aggregation)
│   └── aggregator.py      # Task distribution, merging, and spatial filtering
├── notebooks/             # Visualization and analysis (Heatmaps, Time-series)
├── main.py                # Pipeline entry point
├── .gitignore             # Optimized rules for large datasets and logs
└── README.md
```

## 🚀 Quick Start

### 1. Prerequisites
Install the required dependencies:
```bash
pip install pandas numpy tables parsl matplotlib seaborn
```
### 2. Data Setup
1. **Raw Data**: Place your RUTH-generated HDF5 files in the `data/raw/` directory. 
2. **Metadata**: Ensure you have a road network metadata file (e.g., `df_meta`) that contains the mapping between OSM nodes and road categories (`highway` types).
3. **Mapping**: The script uses an `edge_to_idx` dictionary to map road segments to a fixed matrix index (0 to N).

### 3. Run the Pipeline
To start the transformation, execute the main entry point:
```bash
python main.py
```

The pipeline will:

1. Initialize the Parsl multi-core executor.
2. Read the raw data in chunks of 1 million rows.
3. Perform dual-metric aggregation.
4. Filter by road type and split by peak hours.
5. Save results to data/processed/.

## 📊 Data Processing Logic

### Metric Conversion
* **Speed (Mean)**: Raw data is collected in meters per second (`speed_mps`). The pipeline calculates the mean speed per interval and converts it to miles per hour (**mph**) using the constant $2.23694$.
* **Flow (Unique Count)**: Traffic flow is defined as the number of unique vehicle IDs (`nunique`) observed on a specific road segment within the time interval.
* **Temporal Filling**: For segments with no vehicle pings during a specific interval, the value is filled with `0` to ensure a dense, continuous spatio-temporal matrix.

### Spatial & Road-Level Filtering
To align with the **LargeST** benchmark, the pipeline filters the original 29k+ road segments. It retains only major road categories defined in the metadata:
* `motorway`
* `trunk`
* `primary`
* `secondary`
  
## ⚡ Performance Optimization

### Vectorized ID Mapping
Instead of using slow row-by-row `.apply()` functions, we utilize a vectorized approach with list comprehensions and tuple-based dictionary lookups. This method achieves a **15x speedup** when mapping millions of FCD pings to road indices.

### Memory-Efficient Chunking
Since raw FCD files can exceed 20M+ rows, the pipeline utilizes `pd.read_hdf` with `start` and `stop` parameters. This allows for processing massive files on machines with limited RAM by only loading specific "chunks" into memory at any given time.

### Parallel Execution (Parsl)
The workload is distributed across all available CPU cores using the **Parsl** library. Each worker processes a distinct chunk of the HDF5 file independently, significantly reducing total processing time.

---
