#!/bin/bash

echo "🛑 正在尝试优雅地关闭 Parsl 和相关进程..."

# 1. 尝试终止 Parsl 核心进程
pkill -u $USER -f "parsl"

# 2. 终止工作节点进程 (RUTH 数据处理产生的)
pkill -u $USER -f "process_worker"

# 3. 终止 IPyParallel 相关的控制进程
pkill -u $USER -f "ipengine"
pkill -u $USER -f "ipcontroller"

# 4. 强制清理可能残留的 Python 处理任务 (根据你的路径过滤，防止误杀其他脚本)
pkill -u $USER -f "python3.10"

echo "🧹 正在清理系统僵尸进程..."
# 等待十秒让系统完成进程回收
sleep 10

# 5. 检查是否还有残留
REMAINING=$(pgrep -u $USER -f "parsl|process_worker" | wc -l)

if [ $REMAINING -eq 0 ]; then
    echo "✅ 所有相关进程已清理干净。"
else
    echo "⚠️ 仍有 $REMAINING 个进程未响应，正在执行强制清理 (kill -9)..."
    pgrep -u $USER -f "parsl|process_worker" | xargs kill -9
    echo "💀 强制清理完成。"
fi
