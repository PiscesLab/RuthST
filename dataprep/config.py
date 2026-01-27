# src/config.py
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
EXPERIMENT_DATA_DIR = BASE_DIR / "data" / "ruth"

# Simulation metadata
SIMULATION_METADATA = {
    "0pc":   {"total_rows": 26183823},
    "10pc":  {"total_rows": 23909726},
    "20pc":  {"total_rows": 22613971},
    "30pc":  {"total_rows": 22076670},
    "40pc": {"total_rows": 21337213},
    "50pc":   {"total_rows": 22154288},
    "60pc":  {"total_rows": 22491537},
    "70pc":  {"total_rows": 23172624},
    "80pc":  {"total_rows": 23826772},
    "90pc": {"total_rows": 24785033},
    "100pc": {"total_rows": 26400677},
}

# 文件名
GRAPHML_NAME = "ostrava_routing_map.graphml" # 请确保文件名一致
FCD_NAME_TEMPLATE = "Ostrava_fcd_history-{}pc.h5" # 用于后续循环处理不同比例

# 转换参数
TIME_INTERVAL = "10s"  # 聚合时间窗口
SIMULATION_START_TIME = "2025-05-22 10:22:17" # RUTH 模拟的基准时间
ROAD_FILTER_THRESHOLD = "0.05"
