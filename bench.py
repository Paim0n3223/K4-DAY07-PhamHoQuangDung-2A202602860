"""
Personal benchmark tool — Day 7 Lab (K4-L3A, chu de dang ky hoc phan).

Chien luoc chunking cua rieng toi: FixedSizeChunker (co overlap).
Khong trung voi thanh vien da chon RecursiveChunker.

Chay:
    python bench.py
Ket qua vua in ra man hinh vua ghi vao ket_qua_benchmark.txt.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

CORPUS_DIR = Path("data/registration")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
OUTPUT_FILE = Path("ket_qua_benchmark.txt")

# 5 query benchmark chinh thuc cua nhom (REPORT_NHOM.md muc 3) — moi thanh vien
# dung chung bo nay de so sanh cong bang giua cac chien luoc chunking.
BENCHMARK_QUERIES = [
    {
        "query": "UIT khóa 20 đăng ký HK1 2026–2027 khi nào?",
        "gold_answer": "23/08/2026, 09:00–16:00",
        "metadata_filter": {"audience": "student"},
    },
    {
        "query": "UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào?",
        "gold_answer": "Trước ngày thi kết thúc học phần 10 ngày",
        "metadata_filter": {"audience": "student"},
    },
    {
        "query": "FTU K63/K64 đăng ký tín chỉ bổ sung khi nào?",
        "gold_answer": "14/09–18/09/2026; mỗi ngày 09:00–22:00",
        "metadata_filter": {"audience": "student"},
    },
    {
        "query": "Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu?",
        "gold_answer": "1.650.000 VNĐ/tín chỉ",
        "metadata_filter": {"audience": "student"},
    },
    {
        "query": "FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào?",
        "gold_answer": "05/08–14/08/2026",
        "metadata_filter": {"audience": "student"},
    },
]


def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """Tach YAML frontmatter (---...---) don gian thanh metadata + phan than."""
    if not raw_text.startswith("---"):
        return {}, raw_text

    parts = raw_text.split("---", 2)
    if len(parts) < 3:
        return {}, raw_text

    _, frontmatter_block, body = parts
    metadata: dict = {}
    for line in frontmatter_block.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, body.strip()


def build_embedder():
    """Chon embedding backend giong main.py: mac dinh mock, doi qua .env neu can."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()

    try:
        if provider == "local":
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        if provider == "openai":
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        if provider == "gemini":
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
    except Exception:
        pass

    return _mock_embed


def load_corpus(corpus_dir: Path) -> list[Document]:
    """Doc tung file .md, tach frontmatter, chunk phan than, tra ve list Document."""
    # Dong chon chunker cua chien luoc rieng — MOI NGUOI CHI DOI DONG NAY.
    chunker = FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    documents: list[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(raw_text)
        chunks = chunker.chunk(body)

        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    id=f"{path.stem}#{i}",
                    content=chunk,
                    metadata={**frontmatter, "doc_id": path.stem},
                )
            )

    return documents


def run_benchmark(store: EmbeddingStore) -> list[str]:
    """Chay 5 query qua search_with_filter, tra ve danh sach dong log de in/ghi file."""
    lines: list[str] = []
    for i, item in enumerate(BENCHMARK_QUERIES, start=1):
        lines.append(f"\n[{i}] Query: {item['query']}")
        lines.append(f"    Gold answer: {item['gold_answer']}")
        lines.append(f"    Filter: {item['metadata_filter']}")

        results = store.search_with_filter(
            item["query"], top_k=3, metadata_filter=item["metadata_filter"]
        )
        if not results:
            lines.append("    (khong co ket qua nao)")
            continue

        for rank, result in enumerate(results, start=1):
            doc_id = result["metadata"].get("doc_id", result["id"])
            preview = result["content"][:150].replace("\n", " ")
            lines.append(
                f"    top-{rank}: score={result['score']:.4f} doc_id={doc_id} chunk_id={result['id']}"
            )
            lines.append(f"             preview: {preview}...")

    return lines


def main() -> int:
    if not CORPUS_DIR.exists():
        print(f"Khong tim thay corpus: {CORPUS_DIR}")
        return 1

    documents = load_corpus(CORPUS_DIR)
    embedder = build_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    store = EmbeddingStore(collection_name="bench_store", embedding_fn=embedder)
    store.add_documents(documents)

    header = [
        "=== Bench — Chien luoc: FixedSizeChunker (co overlap) ===",
        f"Chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}",
        f"Embedding backend: {backend_name}",
        f"So chunk da nap: {store.get_collection_size()}",
    ]

    body = run_benchmark(store)

    output_lines = header + body
    output_text = "\n".join(output_lines)

    print(output_text)
    OUTPUT_FILE.write_text(output_text + "\n", encoding="utf-8")
    print(f"\nDa ghi ket qua vao {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
