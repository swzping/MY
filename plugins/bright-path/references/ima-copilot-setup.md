# IMA Copilot MCP 设置说明

Bright Path 通过本机 MCP 服务连接 IMA Copilot。插件本身只声明连接地址，不保存账号认证信息。

## 连接地址

Bright Path 的 `.mcp.json` 默认连接：

```text
http://127.0.0.1:8081/mcp
```

## 推荐 MCP Server

可使用社区项目：

```text
https://github.com/highkay/tencent-ima-copilot-mcp
```

该项目提供腾讯 IMA Copilot 的 MCP server，支持 HTTP 传输，常用工具包括：

- `ask`
- `ask_with_kb`

## 必需环境变量

不要把这些值写进插件文件。请只在本机 shell、`.env` 或 Docker 环境变量中配置：

```text
IMA_X_IMA_COOKIE
IMA_X_IMA_BKN
IMA_KNOWLEDGE_BASE_ID
```

多知识库模式可使用：

```text
IMA_KNOWLEDGE_BASE_IDS
```

## Docker 启动示例

```bash
docker run -d \
  --name ima-copilot-mcp \
  -p 8081:8081 \
  -e IMA_X_IMA_COOKIE="your_x_ima_cookie_here" \
  -e IMA_X_IMA_BKN="your_x_ima_bkn_here" \
  -e IMA_KNOWLEDGE_BASE_ID="your_knowledge_base_id_here" \
  --restart unless-stopped \
  highkay/tencent-ima-copilot-mcp:latest
```

## 本地启动示例

```bash
git clone https://github.com/highkay/tencent-ima-copilot-mcp.git
cd tencent-ima-copilot-mcp
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env` 后启动：

```bash
python run.py
```

或：

```bash
fastmcp run ima_server_simple.py:mcp --transport http --host 127.0.0.1 --port 8081
```

## 如何获取认证信息

1. 打开 `https://ima.qq.com` 并登录。
2. 打开浏览器开发者工具的 Network 面板。
3. 在 IMA 中发送一条消息。
4. 找到 `/cgi-bin/assistant/qa` 请求。
5. 从 Request Headers 中复制：
   - `x-ima-cookie` -> `IMA_X_IMA_COOKIE`
   - `x-ima-bkn` -> `IMA_X_IMA_BKN`

## 检查

服务启动后，确认 MCP 端点可用：

```text
http://127.0.0.1:8081/mcp
```

如果 Codex 无法调用 `ima-copilot` 工具，优先检查：

- Docker 或 Python 服务是否正在运行。
- 端口是否为 `8081`。
- `.mcp.json` 中的 URL 是否一致。
- IMA 认证信息是否过期。
- 是否配置了知识库 ID。
