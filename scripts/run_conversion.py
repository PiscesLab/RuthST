# scripts/run_conversion.py
import os
import sys
# 确保能找到 src 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataprep.graph_logic import generate_graph_metadata, generate_adjacency_matrix
from dataprep.aggregator import run_h5_conversion

def main():
    # 1. 运行第一阶段 (获取映射表)
    G, edge_to_idx, df_meta = generate_graph_metadata()
    generate_adjacency_matrix(G, edge_to_idx, df_meta)
    
    # 2. 运行第二阶段 (处理指定的 Portion)
    # 你可以手动指定，或者写个循环处理所有比例
    portion = "50pc" 
    run_h5_conversion(portion, edge_to_idx, df_meta)

if __name__ == "__main__":
    main()
