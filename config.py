import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# Overleaf 配置
OVERLEAF_BASE_URL = os.getenv("OVERLEAF_BASE_URL", "https://example.com")
# OVERLEAF_API_TOKEN = os.getenv("OVERLEAF_API_TOKEN")
OVERLEAF_EMAIL = os.getenv("OVERLEAF_EMAIL")
OVERLEAF_PASSWORD = os.getenv("OVERLEAF_PASSWORD")

# 验证必要的配置
if not OVERLEAF_BASE_URL:
    raise ValueError("OVERLEAF_BASE_URL 必须设置")

# if not (OVERLEAF_API_TOKEN or (OVERLEAF_EMAIL and OVERLEAF_PASSWORD)):
if not (OVERLEAF_EMAIL and OVERLEAF_PASSWORD):
    raise ValueError("必须提供 EMAIL/PASSWORD") 