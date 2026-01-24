# src/aggregator.py
import pandas as pd
import numpy as np
import parsl
import os
from src.parsl_config import parsl_config
from src.parsl_worker import process_h5_chunk
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, TIME_INTERVAL

def run_h5_conversion(portion_name, edge_to_idx):
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
    
    # 对齐所有 29735 个路段
    num_nodes = len(edge_to_idx)
    final_df = final_df.reindex(columns=range(num_nodes)).fillna(0)
    
    # 单位转换: mps -> mph
    final_df = final_df * 2.23694
    
    # 保存结果
    output_path = PROCESSED_DATA_DIR / f"his_portion_{portion_name}.h5"
    final_df.to_hdf(output_path, key='data', mode='w')
    
    parsl.clear()
    print(f"✅ 转换完成！输出: {output_path}")
