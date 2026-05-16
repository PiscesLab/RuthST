# src/graph_logic.py
import networkx as nx
import pandas as pd
import numpy as np
import os
from dataprep.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPERIMENT_DATA_DIR, GRAPHML_NAME

def generate_graph_metadata(city="ostrava"):
    """
    解析 GraphML，生成 meta.csv 和索引映射表
    """
    #graph_path = RAW_DATA_DIR / GRAPHML_NAME
    graph_path = RAW_DATA_DIR / f"{city}_routing_map.graphml"
    print(f"正在加载路网文件: {graph_path}")
    
    # 1. 使用 networkx 加载路网
    G = nx.read_graphml(graph_path)
    
    phys_nodes = G.number_of_nodes()
    phys_edges = G.number_of_edges()

    # 密度公式: E / (V * (V - 1))
    phys_density = nx.density(G)
    # 平均度数: 每个路口平均连着几条路
    avg_degree = phys_edges / phys_nodes if phys_nodes > 0 else 0

    # 2. 提取边（在模型中作为节点）
    # RUTH 的边通常由 (u, v, key) 唯一标识
    edges_list = []
    edge_to_idx = {} # 建立 (u, v, key) -> ID2 的映射
    
    for i, (u, v, key, data) in enumerate(G.edges(keys=True, data=True)):
        # 计算中心点：(起点坐标 + 终点坐标) / 2
        # 注意：OSMnx 导出的 graphml 坐标通常在 node 的 'x' (lng) 和 'y' (lat) 属性中
        node_u = G.nodes[u]
        node_v = G.nodes[v]
        
        center_lat = (float(node_u['y']) + float(node_v['y'])) / 2
        center_lng = (float(node_u['x']) + float(node_v['x'])) / 2
        
        edge_id = f"{u}_{v}_{key}"
        edge_to_idx[(str(u), str(v), key)] = i

        # 辅助函数：处理可能存在的 list 型属性并转为 string
        def get_attr(attr_name, default='0'):
            val = data.get(attr_name, default)
            if isinstance(val, list):
                return str(val[0])
            return str(val)

        # 3. 提取并清洗 maxspeed (将 "50 km/h" 或 ["50", "30"] 统一转为数字)
        raw_speed = get_attr('maxspeed', '0')
        speed_digits = "".join(filter(str.isdigit, raw_speed))
        clean_maxspeed = int(speed_digits) if speed_digits else 0
        
        edges_list.append({
            'ID': edge_id,
            'lat': center_lat,
            'lng': center_lng,
            'u': u,
            'v': v,
            'key': key,
            'highway': data.get('highway', 'unclassified'),
            'maxspeed': data.get('maxspeed', '0'),
            'lanes': data.get('lanes', '1'),
            'length': float(data.get('length', 0)),
            'oneway': data.get('oneway', '0'),
            'bridge': data.get('bridge', '0'),
            'tunnel': data.get('tunnel', '0'),
            'junction': data.get('junction', 'none'),
            'width': data.get('width', '0'),
            'ID2': i
        })

    df_meta = pd.DataFrame(edges_list)
    
    model_nodes = len(df_meta)

    # 保存包含 15+ 列的 meta.csv
    meta_path = PROCESSED_DATA_DIR / "meta.csv"
    # 我们保留所有列，这比 LargeST 更丰富
    df_meta.to_csv(meta_path, index=False)
    print(f"成功生成 meta.csv, 包含 {len(df_meta)} 个节点，属性列数: {len(df_meta.columns)}")

    print(f"--- 物理路网属性 (Physical Road Network) ---")
    print(f"路口总数 (Intersection Nodes): {phys_nodes}")
    print(f"路段总数 (Road Edges): {phys_edges}")
    print(f"平均度数 (Avg Degree): {avg_degree:.2f}")
    print(f"网络密度 (Graph Density): {phys_density:.6f}")

    print(f"\n--- 模型训练属性 (Model/LargeST Layer) ---")
    print(f"模型节点总数 (Total Sensors/Nodes): {model_nodes}")
    print(f"说明: 物理路网的 {phys_edges} 条边已被映射为模型的 {model_nodes} 个预测目标。")
    
    return G, edge_to_idx, df_meta

def generate_adjacency_matrix(G, edge_to_idx, df_meta, city="ostrava", main_roads=['motorway', 'trunk', 'primary', 'secondary']):
    """
    根据路网拓扑构建邻接矩阵 ruth_adj_matrix.npy
    """
    # 1. 筛选主干道
    df_meta_filtered = df_meta[df_meta['highway'].isin(main_roads)].copy()
    num_nodes = len(df_meta_filtered)

    # 2. 建立新旧索引映射：(u, v, key) -> 0 到 num_nodes-1 的连续索引
    # 这一步至关重要，确保矩阵维度对齐
    edge_to_new_idx = {}
    for i, (original_idx, row) in enumerate(df_meta_filtered.iterrows()):
        # 构造与 G.out_edges 匹配的 key
        edge_key = (str(row['u']), str(row['v']), row['key'])
        edge_to_new_idx[edge_key] = i

    # 3. 初始化全 0 矩阵 (2453, 2453)
    adj_matrix = np.zeros((num_nodes, num_nodes))

    print(f"正在为 {num_nodes} 条主干道构建邻接矩阵...")

    # 4. 填充连接关系
    for i, (original_idx, row) in enumerate(df_meta_filtered.iterrows()):
        current_v = row['v']
        
        # 寻找从当前路段终点 (v) 出发的所有边
        for _, next_v, next_key in G.out_edges(current_v, keys=True):
            next_edge_tuple = (str(current_v), str(next_v), next_key)
            
            # 如果下一条边也在我们的主干道列表里
            if next_edge_tuple in edge_to_new_idx:
                j = edge_to_new_idx[next_edge_tuple]
                adj_matrix[i, j] = 1 # 有向边连接

    # 保存 adj.npy
    adj_path = PROCESSED_DATA_DIR / "ruth_adj_matrix.npy"
    np.save(adj_path, adj_matrix)

    exp_path = EXPERIMENT_DATA_DIR / "ruth_adj_matrix.npy"
    np.save(exp_path, adj_matrix)
    
    # 计算稀疏度
    sparsity = (np.count_nonzero(adj_matrix) / (num_nodes ** 2)) * 100
    print(f"成功生成 adj_matrix.npy, 形状: {adj_matrix.shape}, 稀疏度: {sparsity:.4f}%")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(EXPERIMENT_DATA_DIR, exist_ok=True)
    
    G, edge_to_idx, df_meta = generate_graph_metadata()
    generate_adjacency_matrix(G, edge_to_idx, df_meta)
