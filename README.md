# Overleaf API 服务

这是一个基于 FastAPI 的 Overleaf API 服务，提供了 LaTeX 文档的编译和管理功能。

## 功能特点

- 项目管理（创建、删除）
- 文件操作（上传、更新、列表）
- LaTeX 文档编译
- PDF 文件下载
- 服务健康检查

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/your-username/overleaf-api.git
cd overleaf-api
```

2. 创建并激活虚拟环境（可选但推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的 Overleaf 认证信息：
```env
OVERLEAF_BASE_URL=https://example.com
OVERLEAF_API_TOKEN=your_api_token_here
OVERLEAF_EMAIL=your_email@example.com
OVERLEAF_PASSWORD=your_password_here
```

## 运行服务

### 开发模式

使用 uvicorn 直接运行（支持代码热重载）：
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式

使用 python 直接运行：
```bash
python app.py
```

或使用 gunicorn（推荐用于生产环境）：
```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## API 文档

服务运行后，可以访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 健康检查
- GET `/health` - 检查服务状态

### 项目管理
- POST `/projects` - 创建新项目
- DELETE `/projects/{project_id}` - 删除项目

### 文件操作
- POST `/projects/{project_id}/files` - 上传文件
- GET `/projects/{project_id}/files` - 获取文件列表
- PUT `/projects/{project_id}/files/{file_id}` - 更新文件内容

### 编译相关
- POST `/projects/{project_id}/compile` - 编译项目
- GET `/projects/{project_id}/pdf` - 获取编译后的 PDF

## 使用示例

```python
import requests

# 基础 URL
base_url = "http://localhost:8000"

# 创建项目
response = requests.post(
    f"{base_url}/projects",
    params={"name": "测试项目"}
)
project_id = response.json()["project_id"]

# 上传 LaTeX 文件
with open("document.tex", "rb") as f:
    response = requests.post(
        f"{base_url}/projects/{project_id}/files",
        files={"file": f}
    )

# 编译项目
response = requests.post(
    f"{base_url}/projects/{project_id}/compile"
)

# 下载 PDF
response = requests.get(
    f"{base_url}/projects/{project_id}/pdf"
)
if response.status_code == 200:
    with open("output.pdf", "wb") as f:
        f.write(response.content)
```

## 项目结构

```
overleaf-api/
├── app.py              # FastAPI 应用主文件
├── config.py           # 配置文件
├── overleaf_client.py  # Overleaf 客户端
├── requirements.txt    # 项目依赖
├── .env               # 环境变量（需要自行创建）
└── README.md          # 项目文档
```

## 注意事项

1. 安全性
   - 不要将 `.env` 文件提交到版本控制系统
   - 在生产环境中使用 HTTPS
   - 考虑添加 API 认证机制

2. 性能
   - 大文件上传可能需要调整服务器配置
   - 编译大型文档时注意超时设置

3. 错误处理
   - 所有 API 端点都包含基本的错误处理
   - 检查日志以排查问题

## 依赖项

- FastAPI: Web 框架
- uvicorn: ASGI 服务器
- python-multipart: 文件上传支持
- python-dotenv: 环境变量管理
- requests: HTTP 客户端

## 许可证

[您的许可证类型]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

[您的名字]

## 更新日志

### v1.0.0
- 初始版本发布
- 实现基本的 Overleaf API 功能
- 添加 FastAPI 服务层