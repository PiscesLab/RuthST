# src/config.py
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# 文件名
GRAPHML_NAME = "ostrava_routing_map.graphml" # 请确保文件名一致
FCD_NAME_TEMPLATE = "Ostrava_fcd_history-{}pc.h5" # 用于后续循环处理不同比例

# 转换参数
TIME_INTERVAL = "1min"  # 聚合时间窗口
SIMULATION_START_TIME = "2025-05-22 10:22:17" # RUTH 模拟的基准时间
ROAD_FILTER_THRESHOLD = "0.05"
