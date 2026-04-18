# ==============================================================================
# 静态知识库引擎 (ChromaDB + BGE-small-zh 嵌入)
# ==============================================================================

import os
import glob
from nonebot import logger

os.environ.setdefault("ORT_DISABLE_CPU_AFFINITY", "1")

import chromadb
from chromadb.utils import embedding_functions

# 知识库文档目录 & ChromaDB 持久化路径
_DOCS_DIR = os.path.join(os.path.dirname(__file__), "../../../data/knowledge/docs")
_CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../../data/knowledge/chroma_db")

_collection = None


def _get_collection():
    """获取或初始化 ChromaDB collection（单例）"""
    global _collection
    if _collection is not None:
        return _collection

    os.makedirs(_CHROMA_DIR, exist_ok=True)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5"
    )

    client = chromadb.PersistentClient(path=os.path.abspath(_CHROMA_DIR))
    _collection = client.get_or_create_collection(
        name="prts_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def ingest_docs():
    """扫描 docs 目录，将新文件写入知识库（增量）"""
    docs_dir = os.path.abspath(_DOCS_DIR)
    if not os.path.isdir(docs_dir):
        os.makedirs(docs_dir, exist_ok=True)
        logger.info(f"📚 [知识库] 文档目录已创建: {docs_dir}，请放入 .txt / .md 文件后重启。")
        return

    files = glob.glob(os.path.join(docs_dir, "**/*.*"), recursive=True)
    txt_files = [f for f in files if f.endswith((".txt", ".md"))]

    if not txt_files:
        logger.info("📚 [知识库] 文档目录为空，跳过索引。")
        return

    collection = _get_collection()
    existing_ids = set(collection.get()["ids"])

    added = 0
    for fpath in txt_files:
        rel = os.path.relpath(fpath, docs_dir)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        if not content:
            continue

        # 按段落分块，每块最多 512 字符
        chunks = _split_text(content, max_len=512)
        for i, chunk in enumerate(chunks):
            doc_id = f"kb_{rel}_{i}"
            if doc_id in existing_ids:
                continue
            collection.add(
                documents=[chunk],
                ids=[doc_id],
                metadatas=[{"source": rel, "chunk_index": i}],
            )
            added += 1

    logger.success(f"📚 [知识库] 索引完成：扫描 {len(txt_files)} 个文件，新增 {added} 个文档块。")


def search_knowledge(query: str, top_k: int = 3) -> list[str]:
    """检索知识库，返回最相关的文档片段列表"""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # ChromaDB cosine distance: 0=完全相同, 2=完全相反; 过滤阈值 < 1.2
    filtered = []
    for doc, dist in zip(docs, distances):
        if dist < 1.2:
            filtered.append(doc)
    return filtered


def _split_text(text: str, max_len: int = 512) -> list[str]:
    """按段落分块，保证每块不超过 max_len"""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) + 2 > max_len:
            if current:
                chunks.append(current)
            # 单段超长则硬切
            while len(p) > max_len:
                chunks.append(p[:max_len])
                p = p[max_len:]
            current = p
        else:
            current = f"{current}\n\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks
