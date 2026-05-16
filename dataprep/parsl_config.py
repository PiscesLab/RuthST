# src/parsl_config.py
from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.config import Config
import multiprocessing

# 自动获取核心数，预留 2 个给系统
n_cores = max(1, multiprocessing.cpu_count() - 2)
#print(f"[Parsl] max_workers_per_node={n_cores}")

parsl_config = Config(
    executors=[
        HighThroughputExecutor(
            label="htex_local",
            # 注意：新版本使用 max_workers_per_node
            max_workers_per_node=n_cores,
            provider=LocalProvider(
                init_blocks=1,
                max_blocks=1,
            ),
        )
    ],
    # 策略设置：如果任务失败不自动重试（方便调试）
    retries=0,
)
