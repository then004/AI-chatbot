# AI Chatbot — Local Open-Source Startup Agent

一个单用户、本地优先的创业研究助手，包含 React/Vite 前端与 FastAPI 后端。应用默认通过 Ollama 在本机运行模型，不需要付费 API。

## 功能

- 项目顾问：项目隔离的持续对话、确认后的记忆
- RAG / 知识库问答：项目私有上传资料 + 公共知识库关键词检索
- 商业计划：预算计算、异步生成、HTML/JSON 报告
- Reddit 市场验证：用户自行配置 Reddit API 后执行；未配置时安全阻断
- 异步任务：上传索引、商业计划、Reddit 研究，带状态和错误信息
- 本地数据存储：SQLite、上传文件和报告均保存在本机

公共 PDF 知识库不随 GitHub 仓库分发。请自行提供拥有再分发权的资料后导入。

## 技术栈

- Frontend: React + Vite
- Backend: FastAPI + Uvicorn
- Storage: SQLite
- Local LLM: Ollama
- PDF extraction: pypdf
- Optional: PRAW for Reddit
- Retrieval: SQLite/关键词检索；当前不是语义向量检索

## 前置条件

- Python 3.11+
- Node.js 18+
- Ollama
- Ollama 模型，例如：

```bash
ollama pull qwen2.5:3b
```

Windows 用户请注意：`uvloop` 不支持 Windows，不要安装它；使用本项目 Web 依赖即可。

## 安装

```powershell
cd "E:\year4\AI chatbot"

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-web.txt

cd web\frontend
npm install
```

## 配置

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

Ollama 默认配置：

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

Reddit 是可选功能。需要用户自行创建 Reddit 应用并填写：

```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=AI-chatbot/0.1
```

不要把真实 `.env`、API key 或 token 提交到 Git。

## 导入公共知识库

将拥有使用权的 PDF 放入任意本地目录。迁移脚本会复制文件、提取文本并幂等写入 SQLite；不会删除源文件：

```powershell
python scripts\migrate_public_knowledge.py --source "D:\\my-knowledge-pdfs"
```

迁移结果会打印成功、跳过和失败统计。公共资料在 Web 中是只读的，不能通过项目接口删除。

## 运行 Web 应用

启动后端：

```powershell
cd "E:\year4\AI chatbot"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="E:\year4\AI chatbot;E:\year4\AI chatbot\web\backend"
python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8100
```

另开终端启动前端：

```powershell
cd "E:\year4\AI chatbot\web\frontend"
npm run dev -- --host 127.0.0.1
```

访问：

```text
http://127.0.0.1:5173
```

也可以使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_web_local.ps1
```

停止：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_web_local.ps1
```

## API 概览

- `GET /api/health`
- `GET/POST /api/projects`
- `GET/POST /api/projects/{id}/messages`
- `GET/POST /api/projects/{id}/uploads`
- `GET /api/projects/{id}/search?q=...`
- `GET /api/knowledge/public`
- `POST /api/projects/{id}/plans`
- `GET /api/projects/{id}/tasks`
- `GET /api/projects/{id}/reports`
- `POST /api/projects/{id}/research/proposals`

## 安全与数据边界

- 默认只监听 `127.0.0.1`，不是公网服务
- 项目资料按 project ID 隔离
- 公共知识库只读，项目用户不能删除
- 用户输入、证据和模型文本在 HTML 报告中会转义，不执行模型 HTML/JavaScript
- Reddit 只有配置凭据后才会访问网络
- 不要上传密码、token、个人身份证明或其他敏感资料
- 数据库、上传文件、报告和运行日志属于本地运行数据，不应提交到 GitHub

## 测试

核心测试：

```powershell
$env:PYTHONPATH="E:\year4\AI chatbot"
python -m unittest discover -s tests -v
```

Web 后端测试：

```powershell
$env:PYTHONPATH="E:\year4\AI chatbot;E:\year4\AI chatbot\web\backend"
python -m unittest discover -s web\backend -v
```

前端构建：

```powershell
cd web\frontend
npm run build
```

## 目录结构

```text
AI chatbot/
├─ core/                         # 结构化计划、预算、检索、报告渲染
├─ web/backend/                  # FastAPI API、SQLite、任务
├─ web/frontend/                 # React/Vite UI
├─ scripts/                     # 启动、停止、知识库迁移
├─ tests/                       # 核心测试
├─ docs/                        # 设计和实施文档
├─ .env.example                 # 配置模板
└─ requirements-web.txt         # Web 最小依赖
```

## License

发布前请根据课程/项目要求补充许可证。当前仓库不自动声明第三方资料或 PDF 的再分发权利。

