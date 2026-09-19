# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Hồ Quang Dũng - 2A202602860
**Nhóm:** ABCD
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có vector embedding trỏ gần như cùng hướng trong không gian nhiều chiều, tức là mô hình cho rằng chúng mang ý nghĩa/ngữ cảnh gần giống nhau — kể cả khi từ ngữ dùng khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên cần đăng ký học phần trước ngày 20/8."
- Câu B: "Trước ngày 20/8, sinh viên phải hoàn tất việc đăng ký các học phần."
- Tại sao tương đồng: cùng diễn đạt một nội dung (hạn đăng ký học phần) dù cấu trúc câu và một phần từ vựng khác nhau — embedding nắm bắt ý nghĩa chứ không so khớp từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên đăng ký học phần qua hệ thống SIS."
- Câu B: "Thư viện mở cửa từ 7 giờ đến 22 giờ mỗi ngày."
- Tại sao khác: hai chủ đề hoàn toàn khác nhau (đăng ký học phần vs. giờ mở cửa thư viện), không chia sẻ ngữ cảnh hay ý nghĩa chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ so sánh **hướng** của vector (ý nghĩa) mà bỏ qua độ dài/độ lớn của vector — vốn thường bị ảnh hưởng bởi độ dài văn bản hoặc cách chuẩn hóa embedding — nên phản ánh đúng mức độ tương đồng ngữ nghĩa hơn; Euclidean distance nhạy với magnitude nên hai câu cùng nghĩa nhưng độ dài khác nhau có thể bị tính là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* số lượng chunk = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = **23**
> *Đáp án:* 23 chunks (đã kiểm lại bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)` → `len(...) == 23`)

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên **25** (ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = 25). Overlap lớn hơn giúp giữ ngữ cảnh liên tục qua ranh giới giữa hai chunk — tránh việc một câu/ý quan trọng bị cắt đôi và mất thông tin khi truy xuất — đánh đổi bằng việc tốn thêm dung lượng lưu trữ và số lượng chunk cần embed.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `(?<=[.!?])\s+` để tách câu ngay sau dấu `.`, `!`, `?` mà **không nuốt mất dấu câu** (khác với `[.!?]\s+` thông thường sẽ làm mất dấu). Sau khi tách, strip khoảng trắng thừa và bỏ chuỗi rỗng, rồi gom `max_sentences_per_chunk` câu liên tiếp thành một chunk. Edge case chưa xử lý: chữ viết tắt (`TS.`, `v.v.`) và số thập phân (`3.14`) sẽ bị coi là ranh giới câu và cắt sai.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy hai chiều theo danh sách separator ưu tiên `["\n\n", "\n", ". ", " ", ""]`: nếu mảnh còn dài hơn `chunk_size`, tách bằng separator hiện tại rồi với mảnh con nào vẫn dài thì gọi đệ quy tiếp với separator kế tiếp (đệ quy xuống sâu); sau đó gom các mảnh nhỏ liền kề nối lại tới sát `chunk_size` bằng chính separator vừa dùng (gom lên), tránh sinh ra hàng trăm chunk vụn. Base case gồm 3 trường hợp: `len(current_text) <= chunk_size` (dừng), `remaining_separators` rỗng (cắt cứng theo `chunk_size`), và separator là `""` (cũng cắt cứng vì không thể `str.split("")`).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Chỉ dùng in-memory (`self._store: list[dict]`), bỏ hẳn nhánh ChromaDB vì test không cần và `requirements.txt` không cài — ép `self._use_chroma = False` để tránh bẫy rẽ nhầm nhánh nếu máy chấm lỡ có `chromadb`. `add_documents` gọi helper `_make_record` để embed nội dung và chuẩn hoá thành record (copy metadata, đảm bảo có `doc_id`) rồi append vào store. `search` gọi helper `_search_records` dùng chung với `search_with_filter`: embed câu query, tính dot product (vector đã chuẩn hoá nên dot product = cosine similarity) với từng record, sắp xếp giảm dần theo score và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc metadata **trước**, search **sau**: `search_with_filter` duyệt `self._store`, giữ lại record nào khớp toàn bộ cặp key-value trong `metadata_filter`, rồi mới đưa tập ứng viên đó qua `_search_records`. Lọc sau khi đã lấy top-k sẽ sai vì có thể mất hết kết quả đúng do k slot đã bị tài liệu không khớp chiếm chỗ. `delete_document` xoá bằng cách lọc lại `self._store`, giữ những record có `metadata['doc_id'] != doc_id`, so sánh độ dài trước/sau để trả về `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba nhịp: kiểm tra store rỗng (trả thông báo, không gọi LLM) → `store.search(question, top_k)` lấy các chunk liên quan → dựng context bằng cách đánh số từng chunk `[1] [2] [3]` kèm `source` (lấy từ `metadata['doc_id']`) → nhét vào prompt cùng chỉ dẫn "chỉ dùng ngữ cảnh được cung cấp, trích dẫn số nguồn, nếu không có thì nói không tìm thấy" → gọi `llm_fn(prompt)`. Cách đánh số nguồn giúp câu trả lời truy vết được về đúng chunk/file (tiêu chí Source Traceability).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.11, pytest-9.0.3, pluggy-1.5.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Sinh viên phải đăng ký học phần trước ngày 23/08/2026." | "Hạn chót ghi danh các môn học là ngày 23 tháng 8 năm 2026." | cao | 0,7142 | Đúng |
| 2 | "Học phí học phần thạc sĩ là 1.650.000 đồng mỗi tín chỉ." | "Mức thu cho mỗi tín chỉ chương trình thạc sĩ vào khoảng 1,65 triệu đồng." | cao | 0,8588 | Đúng |
| 3 | "Sinh viên đăng ký học phần qua hệ thống UMS." | "Thư viện trường mở cửa từ 7 giờ sáng đến 10 giờ tối." | thấp | 0,2325 | Đúng |
| 4 | "Quy định về hủy học phần đã đăng ký của sinh viên UEH." | "Chính sách học bổng khuyến khích học tập dành cho sinh viên xuất sắc." | thấp | 0,2500 | Đúng |
| 5 | "Sinh viên khóa 60 đến khóa 64 đăng ký học tập từ ngày 05/8 đến 14/8/2026." | "Sinh viên khóa 65 đăng ký học tập từ ngày 12/9 đến 13/9/2026." | thấp | 0,9176 | **Sai** |

> Đo bằng `compute_similarity` (`src/chunking.py`) trên embedding thật `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, ngưỡng quy ước: ≥0,5 = cao, <0,5 = thấp.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 bất ngờ nhất: hai câu nói về **hai khóa sinh viên khác nhau với mốc thời gian hoàn toàn khác nhau**, tôi dự đoán "thấp" vì nội dung thực tế (thông tin cần trả lời đúng) khác nhau — nhưng điểm thực tế lại **cao nhất trong cả 5 cặp** (0,9176), cao hơn cả hai cặp paraphrase thật sự đồng nghĩa (0,71 và 0,86). Lý do: hai câu dùng gần như cùng một khung cú pháp và từ vựng ("sinh viên khóa... đăng ký học tập từ ngày... đến ngày..."), nên embedding coi chúng gần như giống hệt nhau về mặt *cấu trúc/chủ đề*, dù khác nhau hoàn toàn về *thực thể cụ thể* (số khóa, ngày tháng). Điều này cho thấy sentence-embedding nắm rất tốt ngữ nghĩa cấp chủ đề nhưng **không đủ nhạy để phân biệt các thực thể/số liệu cụ thể** khi câu có cùng khuôn mẫu — đúng nguyên nhân gốc của failure case đã phát hiện ở mục 5 bên dưới (câu hỏi về khóa 60–64 bị model xếp nhầm sang tài liệu nói về khóa 65).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chạy với embedding thật: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`). Chấm theo **2 mức** (không chỉ xem đúng tài liệu, mà kiểm chuỗi đặc trưng của gold answer có thật trong nội dung chunk hay không) theo `docs/SCORING.md`: 2đ nếu chunk chứa đáp án ở top-1, 1đ nếu ở top-2/3, 0đ nếu vắng.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score (top-1) | Có liên quan không? (Relevant) | Điểm rubric (2/1/0) |
|---|-------|--------------------------------|-------|-----------|-----|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | `uit-dieu-chinh...#0` — đoạn mở đầu, đúng tài liệu nhưng **chưa có ngày cụ thể** | 0,7196 | Đúng tài liệu, sai chunk — đáp án "23/08/2026" nằm ở `#1` (rank 3) | 1đ |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | `ueh-dang-ky-hoc-phan-thac-si-dot1-2026#8` — **sai tài liệu** (nói về học phí dự thính, không phải quy định hủy học phần) | 0,7702 | Không — đáp án đúng ("trước ngày thi kết thúc học phần 10 ngày") nằm ở `ueh-quy-dinh...#12`, rank 2 | 1đ |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | `ftu-thoi-khoa-bieu...#0` — đúng tài liệu nhưng chỉ là đoạn mở đầu, chưa có mốc ngày | 0,6146 | Đúng tài liệu, sai chunk — đáp án "14/09–18/09/2026" nằm ở `#1` (rank 3) | 1đ |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | `ueh-dang-ky-hoc-phan-thac-si-dot1-2026#1` — đúng tài liệu, nói về mục tiêu chương trình, chưa có số học phí | 0,6882 | Đúng tài liệu, sai chunk — đáp án "1.650.000 VNĐ/tín chỉ" nằm ở `#8` (rank 2) | 1đ |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | `ftu-thoi-khoa-bieu...#0` — **sai tài liệu** (thông báo TKB K65, không phải thông báo điều chỉnh khóa 60–64) | 0,7806 | Không — đáp án đúng ("05/08–14/08/2026") nằm ở `ftu-dieu-chinh...#0`, rank 2 | 1đ |

**Bao nhiêu câu hỏi trả về chunk có liên quan (chứa đáp án thật) trong top-3?** 5 / 5 — nhưng **0/5** ở đúng vị trí top-1, nên điểm rubric chỉ đạt **5/10** (mỗi câu 1đ vì đáp án luôn rơi vào rank 2–3, không bao giờ rank 1).

**Mẫu lỗi lặp lại ở cả 5 câu:** chunk đầu tiên của mỗi tài liệu (`#0`, đoạn mở đầu/tiêu đề — đúng chủ đề nhưng không có số liệu cụ thể) luôn được xếp hạng cao hơn chunk thực sự chứa đáp án. Cosine similarity đo độ giống **chủ đề**, không đo **mật độ thông tin trả lời được** — đây là failure case chính, chi tiết ở `REPORT_NHOM.md` mục 4.

> Nguồn số liệu: chạy `python bench.py` với `EMBEDDING_PROVIDER=local` (sentence-transformers đa ngữ), xem đầy đủ trong `ket_qua_benchmark.txt`. Lần chạy trước bằng `MockEmbedder` (băm MD5, không mang ngữ nghĩa) cho kết quả nhiễu hơn — bảng trên đã thay bằng số liệu thật theo yêu cầu CP6.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Điền/bổ sung sau buổi demo trực tiếp 3:25–4:00 — phần dưới là quan sát sơ bộ từ việc đối chiếu kết quả trong nhóm trước demo, cần cập nhật lại sau khi nghe phần trình bày thật của Khánh và Khang.)* Đối chiếu với `RecursiveChunker` của Khánh cho thấy tách theo `\n\n`/`\n`/`. ` trước rồi mới cắt cứng giữ được trọn vẹn câu chứa mốc thời gian/số liệu trong một chunk, khác với `FixedSizeChunker` của tôi hay cắt ngang đúng lúc câu chứa đáp án nằm giữa ranh giới 500 ký tự. Bài học: chọn chiến lược chunking nên dựa vào **cấu trúc thật của văn bản nguồn** (văn bản hành chính có điều/khoản, đoạn) chứ không chỉ dựa vào kích thước chunk mong muốn.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 5 / 10 *(rubric 2/1/0 mỗi câu — cả 5 câu đạt 1đ: đúng tài liệu trong top-3 nhưng chưa đúng ở top-1)* |
| **Tổng phần cá nhân** | **55 / 60** |
