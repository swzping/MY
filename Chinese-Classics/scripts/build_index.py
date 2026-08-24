import os
import json
from typing import List, Dict
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import structlog

# 配置日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# 配置嵌入模型
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-m3"
)

def load_iching_data(file_path: str) -> List[Document]:
    """
    加载周易数据并转换为Document对象
    """
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 简单按卦分割
        sections = content.split('\n\n')
        for section in sections:
            if section.strip():
                doc = Document(
                    text=section,
                    metadata={"source": "iching", "type": "classic"}
                )
                documents.append(doc)
    logger.info("loaded_iching_data", count=len(documents))
    return documents

def load_json_data(file_path: str, data_type: str) -> List[Document]:
    """
    加载JSON数据（星座/生肖）并转换为Document对象
    """
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            doc = Document(
                text=json.dumps(item, ensure_ascii=False),
                metadata={"source": data_type, "name": item.get("name")}
            )
            documents.append(doc)
    logger.info(f"loaded_{data_type}_data", count=len(documents))
    return documents

def build_index():
    """
    构建索引并写入Milvus
    """
    try:
        # 1. 加载数据
        iching_docs = load_iching_data("data/iching.txt")
        horoscope_docs = load_json_data("data/horoscope.json", "horoscope")
        zodiac_docs = load_json_data("data/zodiac.json", "zodiac")
        
        all_docs = iching_docs + horoscope_docs + zodiac_docs
        
        # 2. 连接Milvus
        # 注意：这里假设Milvus已经启动，如果本地没有Docker环境，这一步会失败
        # 为了演示代码逻辑，这里添加try-except块
        try:
            vector_store = MilvusVectorStore(
                uri="http://localhost:19530",
                collection_name="chinese_classics",
                dim=1024,
                overwrite=True
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 3. 构建索引
            index = VectorStoreIndex.from_documents(
                all_docs,
                storage_context=storage_context,
                transformations=[SentenceSplitter(chunk_size=512)]
            )
            
            logger.info("index_build_success", total_docs=len(all_docs))
            return index
        except Exception as e:
            logger.error("milvus_connection_failed", error=str(e))
            logger.info("falling_back_to_local_storage")
            
            # 降级方案：使用本地存储
            index = VectorStoreIndex.from_documents(
                all_docs,
                transformations=[SentenceSplitter(chunk_size=512)]
            )
            index.storage_context.persist(persist_dir="./storage")
            logger.info("local_index_build_success")
            return index

    except Exception as e:
        logger.error("index_build_failed", error=str(e))
        raise

if __name__ == "__main__":
    build_index()
