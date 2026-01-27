# src/parsl_worker.py
import pandas as pd
import numpy as np
from parsl.app.app import python_app

@python_app
def process_h5_chunk(file_path, start_row, row_count, edge_to_idx, time_interval='1min'):
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

    # 自动识别车辆 ID 列
    veh_col = 'veh_id' if 'veh_id' in df.columns else 'vehicle_id'

    # --- 核心修改：双指标聚合 ---
    # 我们对 speed_mps 取均值，对 veh_id 取 nunique (唯一车辆数)
    res = df.groupby([pd.Grouper(key='timestamp', freq=time_interval), 'idx']).agg({
        'speed_mps': 'mean',
        veh_col: 'nunique'
    }).unstack()

    # 5. 实时清洗
    # 注意：多指标聚合后，res 的列是 MultiIndex
    res = res.fillna(0)
    return res
