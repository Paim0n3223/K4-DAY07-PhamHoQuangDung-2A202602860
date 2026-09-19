from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin liên quan trong knowledge base."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin liên quan trong knowledge base."

        context_lines = []
        for i, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id", result["id"])
            context_lines.append(f"[{i}] (source: {source}) {result['content']}")
        context = "\n".join(context_lines)

        prompt = (
            "Trả lời câu hỏi chỉ dựa trên ngữ cảnh dưới đây. "
            "Trích dẫn số nguồn (vd. [1]) cho mỗi thông tin bạn dùng. "
            "Nếu ngữ cảnh không có câu trả lời, hãy nói rõ là không tìm thấy.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
