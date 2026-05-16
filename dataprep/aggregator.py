# src/aggregator.py
import pandas as pd
import numpy as np
import parsl
import os
import time
#from dataprep.parsl_config import parsl_config
from dataprep.parsl_config_eval import make_parsl_config
from dataprep.parsl_worker import process_h5_chunk
from dataprep.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SIMULATION_METADATA, TIME_INTERVAL

def run_h5_conversion(portion_name, edge_to_idx, df_meta, workers=4, city="ostrava", chunk_size=2000000):
    """
    入口函数：并行处理 H5 并生成 his.h5
    """
    # 启动 Parsl
    #parsl.load(parsl_config)
    parsl.load(make_parsl_config(workers))
    
    #input_file = RAW_DATA_DIR / f"Ostrava_fcd_history-{portion_name}.h5"
    input_file = RAW_DATA_DIR / f"{city}_fcd_history-{portion_name}.h5"

    #total_rows = 26183823  # 刚才探测到的总数
    meta = SIMULATION_METADATA.get(portion_name)
    if meta is None:
        with pd.HDFStore(input_file) as store:
            total_rows = store.get_storer("fcd").nrows
    else:
        total_rows = meta["total_rows"]
    #total_rows = SIMULATION_METADATA.get(portion_name)["total_rows"]
    #chunk_size = 1000000   # 每份 100 万行
    
    print(f"🚀 开始转换 {portion_name}, 总行数: {total_rows}, chunk_size={chunk_size}")
    
    futures = []
    for start in range(0, total_rows, chunk_size):
        f = process_h5_chunk(
            str(input_file), 
            start, 
            chunk_size, 
            edge_to_idx, 
            time_interval=TIME_INTERVAL
        )
        futures.append(f)
    
    print(f"已分发 {len(futures)} 个 Parsl 任务，等待中...")

    collect_start = time.time()
    # --- 1. 收集并合并结果 ---
    results = [f.result() for f in futures if f.result() is not None]
    collect_end = time.time()
    print(f"[Timing] task_result_collect_sec={collect_end - collect_start:.2f}")

    # 第一次 concat 会得到 MultiIndex 列: (speed_mps, idx) 和 (veh_id, idx)
    # 使用 mean() 合并相同时间步的数据
    merge_start = time.time()
    combined_df = pd.concat(results).groupby(level=0).mean()
    merge_end = time.time()
    print(f"[Timing] merge_sec={merge_end - merge_start:.2f}")

    # --- 2. 准备空间过滤索引 ---
    main_roads = ['motorway', 'trunk', 'primary', 'secondary']
    target_indices = df_meta[df_meta['highway'].isin(main_roads)].index
    #target_indices = df_meta.index

    # --- 3. 拆分 Speed 和 Flow 并分别处理 ---

    # A. 处理速度 (Speed)
    # 从 MultiIndex 中提取 speed_mps 分支
    speed_df = combined_df['speed_mps'].reindex(columns=target_indices).fillna(0)
    speed_df = speed_df * 2.23694  # mps(m/s) -> mph

    # B. 处理流量 (Flow)
    # 提取车辆数分支 (假设 worker 里叫 veh_id)
    veh_col = 'veh_id' if 'veh_id' in combined_df.columns else 'vehicle_id'
    flow_df = combined_df[veh_col].reindex(columns=target_indices).fillna(0)

    # --- 4. 方案 B：双峰切割并保存 ---
    #periods = {
    #    "morning": ("2025-04-04 05:00:00", "2025-04-04 10:00:00"),
    #    "evening": ("2025-04-04 14:00:00", "2025-04-04 17:00:00")
    #}
    if city == "cbr":
        periods = {"full": (speed_df.index.min(), speed_df.index.max())}
    else:
        periods = {
            "morning": ("2025-04-04 05:00:00", "2025-04-04 10:00:00"),
            "evening": ("2025-04-04 14:00:00", "2025-04-04 17:00:00")
        }
    write_start = time.time()

    for name, (start, end) in periods.items():
        # 切割速度数据并保存
        s_peak = speed_df.loc[start:end].copy()
        s_output = PROCESSED_DATA_DIR / f"his_{portion_name}_{TIME_INTERVAL}_{name}_speed.h5"
        s_peak.to_hdf(s_output, key='data', mode='w')

        # 切割流量数据并保存
        f_peak = flow_df.loc[start:end].copy()
        f_output = PROCESSED_DATA_DIR / f"his_{portion_name}_{TIME_INTERVAL}_{name}_flow.h5"
        f_peak.to_hdf(f_output, key='data', mode='w')

        print(f"✅ {name} 任务完成: Speed {s_peak.shape}, Flow {f_peak.shape}")
    write_end = time.time()
    print(f"[Timing] filter_split_write_sec={write_end - write_start:.2f}")
    parsl.clear()
