# 国学命理智能体 (Chinese Classics Agent) 学习文档

本文档旨在帮助开发者从零开始理解并构建一个基于 **LangGraph**、**LlamaIndex**、**FastAPI** 和 **React** 的全栈 AI 智能体应用。本项目融合了传统国学智慧（周易、星座、八字等）与现代 AI 技术。

---

## 📚 1. 项目架构概览

本项目采用经典的前后端分离架构：

*   **前端 (Frontend)**: React + TypeScript + Vite + Ant Design + Tailwind CSS
    *   负责用户界面交互、流式消息渲染。
*   **后端 (Backend)**: Python + FastAPI + LangChain + LangGraph + LlamaIndex
    *   **FastAPI**: 提供 HTTP API 接口，处理请求与响应。
    *   **LangChain**: 提供 LLM（大语言模型）调用、Prompt 管理等基础能力。
    *   **LangGraph**: 核心 Agent 编排引擎，用于构建有状态、多步骤的 AI 工作流。
    *   **LlamaIndex**: 专注于 RAG (检索增强生成)，负责管理和检索私有知识库。

---

## 🛠️ 2. 核心技术栈解析

### 2.1 LangGraph (Agent 编排)

LangGraph 是 LangChain 推出的用于构建有状态、多 Actor 应用的库。它基于图论（Graph）概念，将 Agent 的运行流程建模为图的**节点 (Nodes)** 和**边 (Edges)**。

#### 核心代码解析

**1. 定义状态 (State)**

`backend/app/agent/state.py`

```python
from typing import Annotated, Sequence, TypedDict, Union, List
import operator
from langchain_core.messages import BaseMessage

# AgentState 定义了 Agent 运行过程中的全局状态
# 所有的 Node 都可以读取和修改这个状态
class AgentState(TypedDict):
    # messages: 存储对话历史，使用 operator.add 进行增量更新（即新消息追加到列表末尾）
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # question: 用户输入的原始问题
    question: str
    # documents: 检索到的相关文档（用于 RAG）
    documents: List[str]
    # generation: LLM 生成的最终答案
    generation: str
```

**2. 定义节点 (Nodes)**

`backend/app/agent/nodes.py`

节点是图中的执行单元，每个节点是一个 Python 函数，接收 `AgentState`，执行逻辑，并返回更新后的状态。

```python
from langgraph.prebuilt import ToolNode
from app.agent.state import AgentState
from app.core.rag import retrieve_documents # 引入 RAG 模块

# ... 初始化 LLM 和 工具 ...

def retrieve(state: AgentState):
    """
    检索节点：负责从向量数据库中查找相关知识
    """
    print("---RETRIEVE---")
    question = state["question"]
    # 调用 LlamaIndex 进行真实检索
    documents = retrieve_documents(question)
    # 返回更新的状态：将检索到的文档存入 documents 字段
    return {"documents": documents}

def generate(state: AgentState):
    """
    生成节点：利用 LLM 和检索到的文档生成回答
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    # 构建 Prompt，包含问题和上下文
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant..."),
        ("human", "Question: {question}\nContext: {context}")
    ])
    chain = prompt | llm
    # 调用 LLM
    response = chain.invoke({"question": question, "context": "\n".join(documents)})
    return {"generation": response.content}

def router_node(state: AgentState):
    """
    路由节点：根据用户意图决定下一步走向
    """
    print("---ROUTER---")
    question = state["question"]
    
    # 简单的关键词匹配路由逻辑
    if any(keyword in question for keyword in ["占卜", "卦"]):
        return {"next_step": "action_iching"} # 走周易工具分支
    elif any(keyword in question for keyword in ["星座"]):
        return {"next_step": "action_horoscope"} # 走星座工具分支
    elif any(keyword in question for keyword in ["知识", "历史", "是什么"]):
        return {"next_step": "retrieve"} # 走知识库检索分支
    else:
        return {"next_step": "generate"} # 默认走通用聊天分支
```

**3. 构建图 (Graph)**

`backend/app/agent/graph.py`

```python
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import retrieve, generate, router_node, ...

def create_graph():
    # 初始化状态图
    workflow = StateGraph(AgentState)

    # 1. 添加节点
    workflow.add_node("router", router_node)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    # ... 添加工具节点 ...

    # 2. 设置入口点 (Entry Point)
    # 图开始运行时，首先执行 router 节点
    workflow.set_entry_point("router")

    # 3. 添加条件边 (Conditional Edges)
    # router 执行完后，根据其返回的 "next_step" 字段决定去哪个节点
    workflow.add_conditional_edges(
        "router",
        lambda x: x["next_step"], # 路由函数
        {
            "action_iching": "action_iching",
            "action_horoscope": "action_horoscope",
            "retrieve": "retrieve",
            "generate": "generate"
        }
    )

    # 4. 添加普通边 (Edges)
    # retrieve 执行完后，总是去往 generate 节点
    workflow.add_edge("retrieve", "generate")
    # generate 执行完后，流程结束 (END)
    workflow.add_edge("generate", END)

    # 编译图，生成可运行的 Runnable 对象
    return workflow.compile()
```

### 2.2 LlamaIndex (RAG 引擎)

LlamaIndex 是构建上下文增强型 LLM 应用的数据框架。

`backend/app/core/rag.py`

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding

def get_index():
    # 配置 Embedding 模型 (这里使用兼容 OpenAI 接口的 DashScope)
    embed_model = OpenAIEmbedding(model="text-embedding-v1", ...)
    
    # 加载本地文档 (支持 txt, pdf, md 等)
    documents = SimpleDirectoryReader("./backend/app/data").load_data()
    
    # 构建向量索引 (Vector Store Index)
    # 这会将文档切块并计算 Embedding，存储在内存中
    index = VectorStoreIndex.from_documents(documents)
    return index

def retrieve_documents(query: str):
    # 检索相关文档片段
    index = get_index()
    retriever = index.as_retriever()
    nodes = retriever.retrieve(query)
    return [node.text for node in nodes]
```

### 2.3 FastAPI & SSE (流式接口)

为了提供类似 ChatGPT 的打字机效果，后端使用了 **Server-Sent Events (SSE)** 技术。

`backend/app/api/endpoints/chat.py`

```python
from sse_starlette.sse import EventSourceResponse
from app.agent.graph import create_graph

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    app = create_graph()
    inputs = {"question": request.message, ...}
    
    async def event_generator():
        # 使用 astream_events 监听 LangGraph 的实时事件
        # version="v1" 是 LangChain 新版流式 API 的规范
        async for event in app.astream_events(inputs, version="v1"):
            kind = event["event"]
            
            # 捕获 LLM 生成的 Token（流式块）
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # 实时推送 Token 给前端
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "token", "content": content})
                    }
            # 捕获工具调用的状态
            elif kind == "on_tool_start":
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "status", "content": f"正在使用工具: {event['name']}..."})
                }
                
    return EventSourceResponse(event_generator())
```

---

## 🚀 3. 如何从 0 开始学习

如果您想掌握本项目相关的技术栈，建议按以下路径学习：

### 阶段一：Python 与 LangChain 基础
1.  **Python 基础**: 熟悉 Python 语法，特别是 `asyncio` (异步编程) 和 `typing` (类型注解)。
2.  **LangChain 核心**: 学习 `PromptTemplate` (提示词模板)、`ChatOpenAI` (模型调用) 和 `LCEL` (LangChain Expression Language)。
    *   *推荐阅读*: LangChain 官方文档的 "Get Started"。

### 阶段二：RAG 与 LlamaIndex
1.  **RAG 概念**: 理解检索增强生成 (Retrieval-Augmented Generation) 的原理。
2.  **LlamaIndex 入门**: 学习如何加载数据 (`SimpleDirectoryReader`)、构建索引 (`VectorStoreIndex`) 和查询 (`QueryEngine`)。
3.  **向量数据库**: 了解 Embedding 和向量检索的基本概念。

### 阶段三：Agent 原理与 LangGraph
1.  **Agent 概念**: 理解什么是 Agent（感知 -> 规划 -> 行动）。
2.  **LangGraph 入门**: 学习 State、Node、Edge 的概念。尝试写一个简单的 "聊天机器人"，能够记录历史消息。
3.  **工具调用 (Tool Use)**: 学习如何让 LLM 调用自定义函数（如本项目中的 `IChingTool`）。

### 阶段四：项目实战 (复刻本项目)
1.  **搭建环境**: 配置 Python 虚拟环境，安装 `langgraph`, `llama-index`, `fastapi`, `uvicorn`。
2.  **实现 RAG**: 使用 LlamaIndex 构建一个简单的本地知识库问答。
3.  **构建 Graph**: 定义 `AgentState`，将 RAG 检索封装为一个 Node。
4.  **接入 API**: 用 FastAPI 包装 Agent，实现 `/chat` 接口。
5.  **对接前端**: 用 React 写一个简单的聊天框，对接后端接口。

---

## 📝 4. 关键文件索引

*   **流程编排**: `backend/app/agent/graph.py` (图的结构)
*   **节点逻辑**: `backend/app/agent/nodes.py` (具体的业务逻辑，含路由和工具调用)
*   **RAG 实现**: `backend/app/core/rag.py` (LlamaIndex 知识库封装)
*   **状态定义**: `backend/app/agent/state.py` (数据结构)
*   **接口定义**: `backend/app/api/endpoints/chat.py` (HTTP 接口与流式处理)
*   **工具实现**: `backend/app/tools/` (各类命理计算工具)

希望这份文档能成为您探索 AI Agent 开发的地图！祝学习愉快！🚀
