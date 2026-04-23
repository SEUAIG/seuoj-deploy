#!/usr/bin/env python3
"""
Generate minimal seed data for agentend (seuoj-qa) so the service can start
without a real knowledge base.  Produces:
  - data/agent-seed/faiss/faiss2.index          (tiny FAISS index, dim=1024)
  - data/agent-seed/faiss/refined_document_chunks.json  (matching docstore)
  - data/agent-seed/qa_bank/answered_questions.json      (empty QA bank)
  - data/agent-seed/knowledge_graph/pre_knowledge_graph.json (empty graph)
"""

import json
import os
import sys

import faiss
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "agent-seed")

EMBED_DIM = 1024  # matches BAAI/bge-m3


def generate_faiss_index():
    """Create a minimal FAISS flat index with one dummy vector."""
    vec = np.zeros((1, EMBED_DIM), dtype="float32")
    index = faiss.IndexFlatIP(EMBED_DIM)  # inner-product (cosine after normalisation)
    index.add(vec)
    path = os.path.join(SEED_DIR, "faiss", "faiss2.index")
    faiss.write_index(index, path)
    print(f"  wrote {path}  (ntotal={index.ntotal}, dim={EMBED_DIM})")


def generate_docstore():
    """Create a single-matching docstore entry for the dummy vector."""
    doc = [
        {
            "chunk_id": 0,
            "title": "示例文档",
            "content": "这是一条用于启动的种子数据，实际使用时请替换为真实知识库。",
            "metadata": {"title": "示例文档"},
            "path_titles": ["种子数据"],
            "path_numbering": ["1"],
        }
    ]
    path = os.path.join(SEED_DIR, "faiss", "refined_document_chunks.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path}  ({len(doc)} entries)")


def generate_qa_bank():
    """Create an empty QA bank (list) so the loader doesn't crash."""
    path = os.path.join(SEED_DIR, "qa_bank", "answered_questions.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)
    print(f"  wrote {path}  (empty)")


def generate_knowledge_graph():
    """Create an empty knowledge graph (graceful fallback, but nice to have)."""
    path = os.path.join(SEED_DIR, "knowledge_graph", "pre_knowledge_graph.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)
    print(f"  wrote {path}  (empty)")


def main():
    print("Generating agentend seed data …")
    generate_faiss_index()
    generate_docstore()
    generate_qa_bank()
    generate_knowledge_graph()
    print("Done.")


if __name__ == "__main__":
    main()
