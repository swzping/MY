from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.tools.iching import IChingTool
from app.tools.horoscope import HoroscopeTool
from app.tools.bazi import BaZiTool
from app.tools.zodiac import ZodiacTool
from app.tools.naming import NamingTool
from app.core.rag import retrieve_documents

# Initialize Tools
tools = [
    IChingTool(),
    HoroscopeTool(),
    BaZiTool(),
    ZodiacTool(),
    NamingTool()
]
# tool_executor = ToolExecutor(tools)

# Initialize LLM
llm = ChatOpenAI(
    model="qwen-max",
    temperature=0,
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    openai_api_key="sk-a9375f14d4a6496dab811cc8d2faf92f"
)

# Define Nodes

async def retrieve(state: AgentState):
    """
    Retrieve documents from vector store.
    """
    print("---RETRIEVE---")
    question = state["question"]
    try:
        documents = retrieve_documents(question)
    except Exception as e:
        print(f"Retrieval error: {e}")
        documents = []
        
    # Fallback if no documents found or error
    if not documents:
        documents = ["暂无相关文档，请直接回答用户问题。"]
        
    return {"documents": documents, "question": question}

async def generate(state: AgentState):
    """
    Generate answer using RAG on retrieved documents (async version)
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state.get("documents", [])
    
    # RAG generation logic
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant for Chinese Classics. Use the following context to answer the question if relevant."),
        ("human", "Question: {question}\nContext: {context}")
    ])
    chain = prompt | llm
    
    # Use async invocation for better performance
    try:
        response = await chain.ainvoke({"question": question, "context": "\n".join(documents)})
        return {"generation": response.content}
    except Exception as e:
        print(f"Generation error: {e}")
        return {"generation": f"抱歉，生成回答时出现错误: {str(e)}"}

def grade_documents(state: AgentState):
    """
    Determines whether the retrieved documents are relevant to the question
    """
    print("---CHECK RELEVANCE---")
    # Mock grading logic
    return {"next_step": "generate"}

def transform_query(state: AgentState):
    """
    Transform the query to produce a better question.
    """
    print("---TRANSFORM QUERY---")
    question = state["question"]
    return {"question": question + " (refined)"}

def action_node(state: AgentState):
    """
    Execute tools.
    """
    print("---ACTION---")
    # In a real LangGraph with ToolNode, this is handled automatically.
    # Here we simulate tool execution if the LLM decided to call a tool.
    messages = state["messages"]
    last_message = messages[-1]
    
    # This is a simplified manual tool execution
    # In production, use LangGraph's prebuilt ToolNode
    return {"messages": []}

def router_node(state: AgentState):
    """
    Route to appropriate node based on intent.
    """
    print("---ROUTER---")
    question = state["question"]
    
    # Simple keyword based routing for demonstration
    if any(keyword in question for keyword in ["占卜", "卦", "吉凶"]):
        return {"next_step": "action_iching"}
    elif any(keyword in question for keyword in ["星座", "运势"]):
        return {"next_step": "action_horoscope"}
    elif any(keyword in question for keyword in ["知识", "介绍", "是什么", "含义", "典故", "历史"]):
        return {"next_step": "retrieve"}
    else:
        return {"next_step": "generate"} # Default to chat

# Specialized Action Nodes for specific tools
def action_iching(state: AgentState):
    tool = IChingTool()
    result = tool.run(state["question"])
    return {"generation": str(result)}

def action_horoscope(state: AgentState):
    tool = HoroscopeTool()
    # Need to extract date from question, mocking it here
    result = tool.run("2000-01-01") 
    return {"generation": str(result)}
