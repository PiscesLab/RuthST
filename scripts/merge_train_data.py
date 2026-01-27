import numpy as np
import os
from pathlib import Path

# --- 配置 ---
portions = [f"{i}pc" for i in range(0, 110, 10)]
#output_dir = Path("data/ruth/morning_speed/")
output_dir = Path("data/ruth/evening_speed/")
#output_dir.mkdir(exist_ok=True)

def combine_largest_datasets():
    all_data = []
    combined_train_idx = []
    combined_val_idx = []
    combined_test_idx = []
    
    current_time_offset = 0
    
    print("开始合并数据...")
    
    for pc in portions:
        # 1. 加载数据矩阵 (T, N, C)
        data_path = f"data/ruth/evening_speed/his_{pc}.npz"
        if not os.path.exists(data_path):
            print(f"⚠️ 跳过 {pc}, 文件不存在")
            continue
            
        with np.load(data_path) as loader:
            data = loader['data'] # 假设内部 key 是 'data'
            m = loader['mean']
            s = loader['std']
            data[..., 0] = data[..., 0] * s + m
            
        # 2. 加载原始索引
        train_idx = np.load(f"data/ruth/evening_speed/idx_train_{pc}.npy")
        val_idx = np.load(f"data/ruth/evening_speed/idx_val_{pc}.npy")
        test_idx = np.load(f"data/ruth/evening_speed/idx_test_{pc}.npy")
        
        # 3. 核心步骤：应用偏移量
        # 使得索引指向全局大矩阵中的正确位置
        combined_train_idx.append(train_idx + current_time_offset)
        combined_val_idx.append(val_idx + current_time_offset)
        combined_test_idx.append(test_idx + current_time_offset)
        
        # 4. 存入数据列表并更新偏移量
        all_data.append(data)
        current_time_offset += data.shape[0]
        
        print(f"✅ 已处理 {pc}: 时间步长度 = {data.shape[0]}, 当前总偏移 = {current_time_offset}")

    # --- 最终拼接 ---
    final_data = np.concatenate(all_data, axis=0)
    mean = final_data[..., 0].mean()
    std = final_data[..., 0].std()
    
    final_data[..., 0] = (final_data[..., 0] - mean) / std
    print(f"📊 计算完毕: Mean={mean:.4f}, Std={std:.4f}")

    # --- 重新保存，加入 mean 和 std ---
    np.savez_compressed(
        output_dir / "his.npz",
        data=final_data,
        mean=mean,
        std=std
    )
    final_train_idx = np.concatenate(combined_train_idx, axis=0)
    final_val_idx = np.concatenate(combined_val_idx, axis=0)
    final_test_idx = np.concatenate(combined_test_idx, axis=0)

    # --- 随机打乱训练集索引 (Shuffle) ---
    # 这对收敛至关重要，让每个 Batch 包含不同渗透率的样本
    np.random.shuffle(final_train_idx)

    # --- 保存结果 ---
    # 为了适配 LargeST，建议保存为 his.npz (包含 data 键)
    np.save(output_dir / "idx_train.npy", final_train_idx)
    np.save(output_dir / "idx_val.npy", final_val_idx)
    np.save(output_dir / "idx_test.npy", final_test_idx)

    print("\n" + "="*30)
    print(f"✨ 合并完成！")
    print(f"📊 最终数据形状: {final_data.shape}")
    print(f"总训练样本数: {len(final_train_idx)}")
    print(f"总验证样本数: {len(final_val_idx)}")
    print(f"总测试样本数: {len(final_test_idx)}")
    print(f"📁 文件保存至: {output_dir.absolute()}")

if __name__ == "__main__":
    combine_largest_datasets()
