# Health & Wellness Agent System

这是一个基于 AI 的大健康养生专家系统，集成了中医养生、营养膳食、心理健康、运动健身和综合健康评估等功能。

## 技术栈

- **前端**: React, TypeScript, Vite, Ant Design, Tailwind CSS
- **后端**: Node.js, Express (可选，目前主要使用 Supabase)
- **数据库 & 认证**: Supabase

## 快速开始

1.  **安装依赖**

    ```bash
    npm install
    ```

2.  **配置环境变量**

    复制 `.env.example` (如果有) 或直接使用已生成的 `.env` 文件。确保包含以下变量：

    ```env
    VITE_SUPABASE_URL=你的Supabase项目URL
    VITE_SUPABASE_ANON_KEY=你的Supabase Anon Key
    ```

3.  **初始化数据库**

    由于自动迁移可能受限，请在 Supabase Dashboard 的 SQL Editor 中运行 `supabase/migrations/20240523000000_initial_schema.sql` 中的 SQL 语句，以创建必要的表和安全策略。

4.  **启动开发服务器**

    ```bash
    npm run dev
    ```

    前端将运行在 `http://localhost:5173`。

## 功能模块

- **中医养生**: 体质辨识、个性化调理方案
- **营养膳食**: 智能食谱推荐、营养分析
- **心理健康**: 情绪识别、冥想训练
- **运动健身**: 运动计划、数据追踪
- **健康评估**: 综合健康报告、风险预警

## 目录结构

- `src/pages`: 页面组件
- `src/components`: 通用组件
- `src/lib`: 工具库 (Supabase client 等)
- `supabase/migrations`: 数据库迁移文件
- `api`: 后端 API (可选)
