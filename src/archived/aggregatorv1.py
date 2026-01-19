# src/aggregator.py
import pandas as pd
import numpy as np
import parsl
import os
from src.parsl_config import parsl_config
from src.parsl_worker import process_h5_chunk
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, TIME_INTERVAL

def run_h5_conversion(portion_name, edge_to_idx, df_meta):
    """
    入口函数：并行处理 H5 并生成 his.h5
    """
    # 启动 Parsl
    parsl.load(parsl_config)
    
    input_file = RAW_DATA_DIR / f"Ostrava_fcd_history-{portion_name}.h5"
    total_rows = 22154288  # 刚才探测到的总数
    chunk_size = 1000000   # 每份 100 万行
    
    print(f"🚀 开始转换 {portion_name}, 总行数: {total_rows}")
    
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
    
    # 收集并合并结果
    results = [f.result() for f in futures if f.result() is not None]
    
    # 合并 DataFrame
    # 这一步会把相同时间、相同路段的均值再次合并（求加权均值或简单均值）
    final_df = pd.concat(results).groupby(level=0).mean()

    # 1. 合并并初步处理
    final_df = pd.concat(results).groupby(level=0).mean()

    # 2. 空间过滤：仅保留主要道路 (在此处过滤掉 2.9w 中的小路)
    # 假设 df_meta 的 index 对应 0-29734 的 idx
    main_roads = ['motorway', 'trunk', 'primary', 'secondary']
    target_indices = df_meta[df_meta['highway'].isin(main_roads)].index

    # 对齐选定的核心路段，而不是全量 29735 个
    final_df = final_df.reindex(columns=target_indices).fillna(0)

    # 3. 单位转换: mps -> mph
    final_df = final_df * 2.23694

    # 4. 方案 B：双峰切割并保存为两个文件
    # 定义早晚高峰时间段
    periods = {
        "morning": ("2025-04-04 05:00:00", "2025-04-04 08:00:00"),
        "evening": ("2025-04-04 14:00:00", "2025-04-04 17:00:00")
    }

    for name, (start, end) in periods.items():
        # 获取对应时段的数据切片
        peak_df = final_df.loc[start:end].copy()

        # 活跃度过滤 (可选)：剔除在该时段几乎无车的路段
        # active_mask = (peak_df > 0).mean() > 0.05
        # peak_df = peak_df.loc[:, active_mask]

        # 分别保存为 morning 和 evening 文件
        output_path = PROCESSED_DATA_DIR / f"his_portion_{portion_name}_5s_{name}.h5"
        peak_df.to_hdf(output_path, key='data', mode='w')
        print(f"✅ 已生成 {name} 数据: {peak_df.shape} -> {output_path}")

    parsl.clear()
