import pandas as pd
import sys
import os
from src.config import RAW_DATA_DIR

def get_trajectory(vehicle_id, filename="Ostrava_fcd_history-50pc.h5"):
    file_path = RAW_DATA_DIR / filename
    
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到原始文件 {file_path}")
        return

    print(f"🔍 正在从 {filename} 中提取车辆 {vehicle_id} 的轨迹...")
    
    try:
        # 使用 where 条件高效读取（Pandas 的 HDFStore 支持查询）
        # 如果 H5 不是 Table 格式，则需要全量读取后过滤
        df = pd.read_hdf(file_path, key='fcd')
        
        # 过滤目标车辆
        traj = df[df['vehicle_id'] == int(vehicle_id)].copy()
        
        if traj.empty:
            print(f"❓ 未找到 ID 为 {vehicle_id} 的车辆数据。")
            return

        # 转换时间戳并排序
        traj['datetime'] = pd.to_datetime(traj['timestamp'], unit='s')
        traj = traj.sort_values('datetime')

        print(f"\n✅ 成功提取！共 {len(traj)} 条记录。")
        print("--- [轨迹数据预览] ---")
        # 显示关键列：时间、位置（节点）、速度
        cols = ['datetime', 'node_from', 'node_to', 'speed_mps', 'active']
        print(traj[cols].to_string(index=False))

        # 简单统计
        avg_speed = traj['speed_mps'].mean()
        print(f"\n📊 统计摘要:")
        print(f"- 平均速度: {avg_speed:.2f} m/s ({avg_speed * 2.23694:.2f} mph)")
        print(f"- 行驶节点数: {traj['node_from'].nunique()}")

    except Exception as e:
        print(f"⚠️ 处理失败: {e}")

if __name__ == "__main__":
    # 你可以从命令行传入 ID，例如: python scripts/get_vehicle_trajectory.py 2
    if len(sys.argv) < 2:
        print("用法: python scripts/get_vehicle_trajectory.py <vehicle_id> [filename]")
    else:
        v_id = sys.argv[1]
        fname = sys.argv[2] if len(sys.argv) > 2 else "Ostrava_fcd_history-50pc.h5"
        get_trajectory(v_id, fname)
