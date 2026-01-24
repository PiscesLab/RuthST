# src/parsl_worker.py
import pandas as pd
import numpy as np
from parsl.app.app import python_app

@python_app
def process_h5_chunk(file_path, start_row, row_count, edge_to_idx, time_interval='15min'):
    """
    Parsl App: 读取 H5 的特定范围并聚合
    """
    # 1. 高效读取 H5 的切片 (使用 start 和 stop 避免内存溢出)
    df = pd.read_hdf(file_path, key='fcd', start=start_row, stop=start_row + row_count)
    
    # 2. 过滤非活跃数据
    df = df[df['active'] == True]
    
    # 3. 映射路段 ID
    # 构造与 edge_to_idx 匹配的 key 字符串
    u = df['node_from'].astype(int).astype(str)
    v = df['node_to'].astype(int).astype(str)
    # 构造 tuple key: ('node_from', 'node_to', 0)
    df_keys = list(zip(u, v, [0]*len(df)))

    # 使用 map 快速映射
    df['idx'] = [edge_to_idx.get(k, -1) for k in df_keys]
    df = df[df['idx'] != -1]

    if df.empty:
        return None

    # 4. 时间聚合
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # 聚合时使用 speed_mps，freq 使用传入的 time_interval
    # 注意：确保不 set_index，直接在 groupby 里指定 key
    res = df.groupby([pd.Grouper(key='timestamp', freq=time_interval), 'idx'])['speed_mps'].mean().unstack()

    # 5. 实时清洗
    res = res.dropna(axis=1, how='all').fillna(0)
    return res
