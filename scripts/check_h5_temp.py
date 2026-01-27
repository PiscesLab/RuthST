import pandas as pd
import sys
import os
from dataprep.config import PROCESSED_DATA_DIR

def check_processed_h5(filename):
    # 自动补全路径
    file_path = PROCESSED_DATA_DIR / filename
    
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return

    print(f"📖 正在读取: {filename}")
    try:
        # 读取数据
        df = pd.read_hdf(file_path)
        
        print("\n--- [基本维度] ---")
        print(f"形状 (Time_Steps, Road_Segments): {df.shape}")
        print(f"时间跨度: {df.index.min()} 至 {df.index.max()}")
        
        print("\n--- [数值统计 (Speed mph)] ---")
        # 统计非 0 值的速度分布（因为 0 通常代表没车）
        active_speeds = df[df > 0]
        print(active_speeds.describe().loc[['mean', 'min', 'max']].mean(axis=1).to_frame(name='Global_Avg'))
        
        print("\n--- [数据完整度] ---")
        zero_ratio = (df == 0).sum().sum() / df.size
        print(f"零值（无车经过）占比: {zero_ratio:.2%}")
        
        print("\n--- [前 5 行 5 列预览] ---")
        print(df.iloc[:5, :5])

    except Exception as e:
        print(f"⚠️ 读取失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/check_h5_temp.py <文件名>")
        print("例如: python scripts/check_h5_temp.py his_portion_50pc.h5")
    else:
        check_processed_h5(sys.argv[1])
