"""配置读取。密钥从 backend/.env 读，禁止写进代码或日志。"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BACKEND_DIR / ".env")

GLM_API_KEY = os.getenv("GLM_API_KEY", "").strip()
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4.7")

# 调用参数基线（照抄 docs/接口契约.md 第 2 节，不得改动）
TIMEOUT_SECONDS = 60
OVERLOAD_RETRIES = 3
OVERLOAD_BACKOFF = [3, 8]
TIMEOUT_RETRIES = 1
CONCURRENCY_LIMIT = 1
