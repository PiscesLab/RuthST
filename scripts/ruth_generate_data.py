import os
import argparse
import numpy as np
import pandas as pd

class StandardScaler():
    def __init__(self, mean, std, eps=1e-8):
        self.mean = mean
        self.std = std
        self.eps = eps

    def transform(self, data):
        # 增加 epsilon 防止分母为 0
        return (data - self.mean) / (self.std + self.eps)

    def inverse_transform(self, data):
        return (data * (self.std + self.eps)) + self.mean

def generate_data_and_idx(df, x_offsets, y_offsets, add_time_of_day, add_day_of_week):
    num_samples, num_nodes = df.shape
    data = np.expand_dims(df.values, axis=-1)
    
    feature_list = [data]
    if add_time_of_day:
        # 核心逻辑：计算该时间点占一天的比例 (0~1)
        time_ind = (df.index.values - df.index.values.astype('datetime64[D]')) / np.timedelta64(1, 'D')
        time_of_day = np.tile(time_ind, [1, num_nodes, 1]).transpose((2, 1, 0))
        feature_list.append(time_of_day)
    if add_day_of_week:
        dow = df.index.dayofweek
        dow_tiled = np.tile(dow, [1, num_nodes, 1]).transpose((2, 1, 0))
        day_of_week = dow_tiled / 7
        feature_list.append(day_of_week)

    data = np.concatenate(feature_list, axis=-1)
    
    min_t = abs(min(x_offsets))
    max_t = abs(num_samples - abs(max(y_offsets)))
    idx = np.arange(min_t, max_t, 1)
    return data, idx

def generate_train_val_test(args):
    # 修改 1：直接读取指定的 H5 文件
    print(f"📖 正在加载 RUTH 数据: {args.input_h5}")
    df = pd.read_hdf(args.input_h5)
    print('Original data shape:', df.shape)

    seq_length_x, seq_length_y = args.seq_length_x, args.seq_length_y
    x_offsets = np.arange(-(seq_length_x - 1), 1, 1)
    y_offsets = np.arange(1, (seq_length_y + 1), 1)

    data, idx = generate_data_and_idx(df, x_offsets, y_offsets, args.tod, args.dow)
    
    num_samples = len(idx)
    num_train = round(num_samples * 0.6)
    num_val = round(num_samples * 0.2)   

    idx_train = idx[:num_train]
    idx_val = idx[num_train: num_train + num_val]
    idx_test = idx[num_train + num_val:]

    # 修改 2：归一化容错处理
    x_train_raw = data[:idx_val[0] - args.seq_length_x, :, 0] 
    # 计算全局均值和标准差
    scaler = StandardScaler(mean=x_train_raw.mean(), std=x_train_raw.std())
    data[..., 0] = scaler.transform(data[..., 0])

    out_dir = os.path.join(args.out_dir, args.dataset_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    # 保存结果
    np.savez_compressed(os.path.join(out_dir, 'his.npz'), data=data, mean=scaler.mean, std=scaler.std)
    np.save(os.path.join(out_dir, 'idx_train.npy'), idx_train)
    np.save(os.path.join(out_dir, 'idx_val.npy'), idx_val)
    np.save(os.path.join(out_dir, 'idx_test.npy'), idx_test)
    print(f"✅ 处理完成！数据已存至: {out_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_h5', type=str, required=True)
    parser.add_argument('--out_dir', type=str, default='data/processed')
    parser.add_argument('--dataset_name', type=str, default='ruth_evening')
    parser.add_argument('--seq_length_x', type=int, default=12)
    parser.add_argument('--seq_length_y', type=int, default=12)
    parser.add_argument('--tod', type=int, default=1)
    parser.add_argument('--dow', type=int, default=1)
    
    args = parser.parse_args()
    generate_train_val_test(args)
