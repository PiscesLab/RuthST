# scripts/check_h5_format.py
import pandas as pd
import h5py
import os
from src.config import RAW_DATA_DIR

def check_h5():
    # 1. 查找文件
    h5_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.h5')]
    
    if not h5_files:
        print(f"❌ 错误：在 {RAW_DATA_DIR} 没找到 H5 文件。当前目录下有：{os.listdir(RAW_DATA_DIR)}")
        return

    target_path = RAW_DATA_DIR / h5_files[0]
    print(f"🔍 正在探测 H5: {target_path}")

    # 2. 探测 H5 内部结构
    with h5py.File(target_path, 'r') as f:
        print("\n--- [H5 内部 Datasets / Groups] ---")
        def print_structure(name, obj):
            if isinstance(obj, h5py.Dataset):
                print(f"  Dataset: {name}, Shape: {obj.shape}, Type: {obj.dtype}")
        f.visititems(print_structure)

        # 3. 尝试读取数据样例
        # 我们假设最有可能的名字是 'fcd' 或 'table'
        keys = list(f.keys())
        if keys:
            first_key = keys[0]
            print(f"\n--- [尝试读取第一个 Key: {first_key}] ---")
            try:
                # 尝试当作 Pandas Table 读取
                df = pd.read_hdf(target_path, key=first_key, start=0, stop=5)
                print(df.head())
                print("\n列名:", df.columns.tolist())
            except:
                print(f"⚠️ 无法直接用 Pandas 读取。这可能是一个原始 NumPy H5。")
                data_sample = f[first_key][0:5]
                print("数据切片样例:\n", data_sample)

        # 4. 统计 Vehicle ID (使用更快的 nunique 逻辑)
        print("📊 正在统计车辆总数 (这可能需要几秒钟)...")
        try:
            # 只读取 vehicle_id 这一列以节省内存
            df_vehicles = pd.read_hdf(target_path, key='fcd', columns=['vehicle_id'])
            total_vehicles = df_vehicles['vehicle_id'].nunique()
            total_records = len(df_vehicles)

            print(f"\n--- [流量统计结果] ---")
            print(f"🚗 独立车辆总数 (Unique Vehicles): {total_vehicles:,}")
            print(f"📝 原始数据总行数 (Total Records): {total_records:,}")
            print(f"📈 平均每辆车产生记录数: {total_records / total_vehicles:.2f}")

        except Exception as e:
            print(f"⚠️ 无法统计 Vehicle ID: {e}")

if __name__ == "__main__":
    check_h5()
