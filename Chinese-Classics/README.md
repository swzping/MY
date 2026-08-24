# 国学命理智能体 (Chinese Classics Agent)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-blue)

一个基于 AI Agent 技术的国学命理咨询平台，集成了周易占卜、星座运势、生肖配对、起名建议、八字命理分析五大核心功能。本项目旨在帮助零基础学习者理解 AI Agent 的全流程开发。

## 🌟 核心功能

- **周易占卜**: 六爻排盘，解析吉凶
- **星座运势**: 西方星象，每日运势
- **生肖配对**: 传统生肖，性格分析
- **八字命理**: 四柱排盘，流年大运
- **起名建议**: 五行八字，吉祥好名

## 🏗️ 技术架构

- **前端**: React 18, TypeScript, Vite, Ant Design, Tailwind CSS
- **后端**: FastAPI, Python 3.11, LangChain, LangGraph
- **AI/LLM**: OpenAI GPT-4, LlamaIndex (RAG)
- **数据库**: PostgreSQL (pgvector), Redis, Milvus
- **部署**: Docker Compose, Kubernetes

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- Node.js 20+ (仅本地开发前端需要)
- Python 3.11+ (仅本地开发后端需要)

### 一键启动 (Docker Compose)

1. 克隆项目
   ```bash
   git clone https://github.com/your-username/chinese-classics-agent.git
   cd chinese-classics-agent
   ```

2. 配置环境变量
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入您的 OPENAI_API_KEY
   ```

3. 启动服务
   ```bash
   docker-compose up -d
   ```

4. 访问应用
   - 前端页面: http://localhost:5173 (开发环境) 或 http://localhost:80 (生产环境)
   - 后端 API: http://localhost:8000/docs
   - Milvus 面板: http://localhost:9091

### 本地开发

#### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

## 📚 文档

- [产品需求文档 (PRD)](docs/product_requirements.md)
- [技术架构文档](docs/technical_architecture.md)

## 🧪 教程 (Notebooks)

请查看 `notebooks/` 目录获取详细的逐步教程：
1. [环境安装](notebooks/01-setup.ipynb)
2. [向量库写入](notebooks/02-vector-store.ipynb)
3. [Agent 调试](notebooks/03-agent-debug.ipynb)

## 📄 许可证

MIT License
