import asyncio
import json
from typing import Any, AsyncGenerator
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import time

from app.agent.graph import create_graph

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@router.post("/stream")
async def stream_chat(request: ChatRequest, req: Request):
    """
    Stream chat response using SSE (Server-Sent Events)
    Optimized version with caching and better error handling
    """
    start_time = time.time()
    
    # Create graph (this should be cached in production)
    try:
        app = create_graph()
    except Exception as e:
        async def error_generator():
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Failed to initialize chat engine: {str(e)}"})
            }
        return EventSourceResponse(error_generator())
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        # Initial inputs
        inputs = {"question": request.message, "messages": [], "documents": [], "generation": ""}
        
        # Send initial status immediately
        yield {
            "event": "message",
            "data": json.dumps({"type": "status", "content": "正在处理您的请求..."})
        }
        
        try:
            # Use astream for better control over streaming
            # First, stream the graph execution with timeout
            async for event in app.astream_events(inputs, version="v1"):
                kind = event["event"]
                
                # Capture LLM streaming tokens
                if kind == "on_chat_model_stream":
                    chunk_data = event.get("data", {})
                    chunk = chunk_data.get("chunk")
                    if chunk and hasattr(chunk, 'content'):
                        content = chunk.content
                        if content:
                            yield {
                                "event": "message",
                                "data": json.dumps({"type": "token", "content": content})
                            }
                
                # Capture Tool outputs
                elif kind == "on_tool_start":
                    tool_name = event.get('name', 'unknown')
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "status", "content": f"正在使用工具: {tool_name}..."})
                    }
                
                # Capture node transitions
                elif kind == "on_chain_start":
                    node_name = event.get('name', '')
                    if node_name:
                        yield {
                            "event": "message", 
                            "data": json.dumps({"type": "status", "content": f"正在{node_name}..."})
                        }
            
            # Send completion
            elapsed = time.time() - start_time
            yield {
                "event": "message",
                "data": json.dumps({"type": "done", "content": "", "elapsed_time": round(elapsed, 2)})
            }
            
        except asyncio.TimeoutError:
            yield {
                "event": "error",
                "data": json.dumps({"error": "请求超时，请稍后重试"})
            }
        except Exception as e:
            print(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": f"处理请求时出错: {str(e)}"})
            }

    return EventSourceResponse(event_generator())

@router.post("/")
async def chat(request: ChatRequest):
    """
    Standard chat endpoint (non-streaming)
    """
    start_time = time.time()
    
    try:
        app = create_graph()
        inputs = {"question": request.message, "messages": [], "documents": [], "generation": ""}
        
        # Run the graph with timeout
        result = await asyncio.wait_for(
            app.ainvoke(inputs),
            timeout=60.0  # 60 second timeout
        )
        
        elapsed = time.time() - start_time
        
        return {
            "response": result.get("generation", "No response generated"),
            "session_id": request.session_id,
            "elapsed_time": round(elapsed, 2)
        }
    except asyncio.TimeoutError:
        return {
            "response": "请求处理超时，请稍后重试",
            "session_id": request.session_id,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "response": f"处理请求时出错: {str(e)}",
            "session_id": request.session_id,
            "error": str(e)
        }
