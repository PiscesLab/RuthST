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
    # 注意：RUTH H5 里的 node_from/to 是 int64，我们的 edge_to_idx 里的 key 也是 str/int 混合
    # 统一转为 (str(u), str(v), 0)
    def get_idx(row):
        key = (str(int(row['node_from'])), str(int(row['node_to'])), 0)
        return edge_to_idx.get(key, -1)
    
    df['idx'] = df.apply(get_idx, axis=1)
    df = df[df['idx'] != -1]
    
    if df.empty:
        return None

    # 4. 时间聚合
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)
    
    # 计算 15min 均值
    # res 形状为 (Time_Steps, Edges)
    res = df.groupby([pd.Grouper(freq=time_interval), 'idx'])['speed_mps'].mean().unstack()

    # 3. 实时过滤
    # 仅保留在当前 chunk 中有数据的列，减少内存占用
    res = res.dropna(axis=1, how='all').fillna(0)
    return res
