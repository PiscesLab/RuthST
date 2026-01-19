import pandas as pd
import h5py
import os
from src.config import RAW_DATA_DIR

def debug_raw_timeline(filename="Ostrava_fcd_history-50pc.h5"):
    file_path = RAW_DATA_DIR / filename
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return

    print(f"🧪 正在分析原始文件时间分布: {filename}")
    
    # 1. 快速读取 timestamp 列
    try:
        # 为了速度，只读取 timestamp 这一列
        df_time = pd.read_hdf(file_path, key='fcd', columns=['timestamp'])
        
        # 转换为 datetime
        df_time['dt'] = pd.to_datetime(df_time['timestamp'], unit='s')
        
        # 2. 按小时统计行数
        timeline = df_time.resample('1H', on='dt').size()
        
        print("\n--- [每小时数据量统计] ---")
        if timeline.empty:
            print("数据为空！")
        else:
            for time, count in timeline.items():
                print(f"{time.strftime('%Y-%m-%d %H:%M')}: {count:,} 条记录")

        # 3. 检查是否有特定的断层
        start_gap = df_time['dt'].min()
        end_gap = df_time['dt'].max()
        print(f"\n📏 原始数据绝对起始: {start_gap}")
        print(f"📏 原始数据绝对结束: {end_gap}")
        
    except Exception as e:
        print(f"💥 读取出错: {e}")

if __name__ == "__main__":
    # 默认检查 50pc 的原始文件
    debug_raw_timeline()
