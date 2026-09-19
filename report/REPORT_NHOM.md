# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** ActionPlan
**Thành viên:**
- Nguyễn Đình Khang - 2A202602584
- Trần Long Khánh - 2A202602538
- Phạm Hồ Quang Dũng - 2A202602860

**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định và lịch đăng ký học phần đại học

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn **quy định và lịch đăng ký học phần đại học** vì đây là nhu cầu gần gũi với sinh viên, có nhiều câu hỏi chứa mốc thời gian/điều kiện cần trả lời chính xác. Nguồn được lấy từ các trang công khai chính thức của UIT, UEH và FTU, tạo được corpus đa trường để kiểm tra metadata filter và khả năng truy vết.

### Danh sách tài liệu (Data Inventory)

| # | Tài liệu | Nguồn | Ngày lấy / phiên bản | Ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | Điều chỉnh thời gian đăng ký HK1 2026–2027 | UIT Portal | 2026-09-19 / not-stated | 1.111 | student, registration, vi |
| 2 | Quy định đăng ký và hủy học phần | UEH Đào tạo | 2026-09-19 / not-stated | 8.712 | student, registration, vi |
| 3 | Quy chế đào tạo theo tín chỉ | FTU QLĐT | 2026-09-19 / 2007-08-15 | 33.265 | all, registration, vi |
| 4 | TKB K65 và đăng ký tín chỉ bổ sung | FTU QLĐT | 2026-09-19 / not-stated | 1.244 | student, registration, vi |
| 5 | Đăng ký học phần thạc sĩ đợt 1/2026 | UEH Đào tạo | 2026-09-19 / not-stated | 12.819 | student, registration, vi |
| 6 | Điều chỉnh đăng ký học tập HK1 2026–2027 | FTU QLĐT | 2026-09-19 / not-stated | 3.792 | student, registration, vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `uit-dieu-chinh-...` | Xóa, truy vết và nhóm chunk theo tài liệu |
| `audience` | enum | `student`, `all` | Loại tài liệu không đúng đối tượng |
| `department` | string | `academic-affairs` | Thu hẹp theo đơn vị quản lý |
| `category` | string | `registration` | Thu hẹp theo nghiệp vụ |
| `source_url` | URL | trang UIT/UEH/FTU | Kiểm chứng câu trả lời |
| `retrieved_at` | date | `2026-09-19` | Theo dõi độ mới dữ liệu |
| `document_version` | string/date | `2007-08-15` | Phân biệt phiên bản quy định |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược | Số lượng chunk | Độ dài TB | Giữ ngữ cảnh? |
|---|---|---:|---:|---|
| `ftu-dieu-chinh-thoi-gian-dang-ky-hoc-tap.md` | FixedSizeChunker (`fixed_size`) | 30 | 689,1 | Trung bình |
|  | SentenceChunker (`by_sentences`) | 10 | 1919,6 | Có, nhưng chunk quá dài |
|  | RecursiveChunker (`recursive`) | 29 | 652,3 | Tốt |
| `ftu-quy-che-dao-tao-tin-chi.md` | FixedSizeChunker (`fixed_size`) | 76 | 692,4 | Trung bình |
|  | SentenceChunker (`by_sentences`) | 64 | 757,1 | Tốt |
|  | RecursiveChunker (`recursive`) | 81 | 597,0 | Tốt |
| `ftu-thoi-khoa-bieu-lich-dang-ky-tin-chi-k65.md` | FixedSizeChunker (`fixed_size`) | 26 | 695,3 | Trung bình |
|  | SentenceChunker (`by_sentences`) | 5 | 3361,0 | Có, nhưng chunk quá dài |
|  | RecursiveChunker (`recursive`) | 25 | 661,2 | Tốt |

> RecursiveChunker giữ ngữ cảnh tốt hơn vì ưu tiên tách theo đoạn văn, xuống dòng và câu, đồng thời vẫn giữ kích thước chunk gần ngưỡng 700 ký tự. FixedSizeChunker có độ dài ổn định nhưng có thể cắt giữa câu hoặc giữa quy định. SentenceChunker giữ nguyên câu nhưng có thể tạo chunk quá dài khi văn bản có ít dấu kết câu hoặc chứa nhiều menu/nhiễu.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Đình Khang**
- **Loại chiến lược:** Custom — HeadingAwareChunker
- **Mô tả & lý do chọn cho chủ đề này:** Tôi chia tài liệu theo heading, Điều hoặc Mục vì quy định đăng ký học phần thường đã được tổ chức theo các phần ngữ nghĩa như thời gian đăng ký, điều kiện, giới hạn tín chỉ và điều chỉnh học phần. Nếu một mục quá dài, tôi dùng RecursiveChunker để chia nhỏ và gắn lại heading vào mọi mảnh con, giúp chunk luôn giữ ngữ cảnh.
- **Code snippet (nếu custom):**
```python
import re

from src.chunking import RecursiveChunker

class HeadingAwareChunker:
    """Tách theo heading hoặc Điều/Mục; section dài dùng recursive fallback."""

    HEADING_PATTERN = re.compile(
        r"^(#{1,6}\s+.+|(?:Điều|Mục)\s+\d+.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches = list(self.HEADING_PATTERN.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks = []
        preamble = text[:matches[0].start()].strip()
        if preamble:
            chunks.extend(
                RecursiveChunker(chunk_size=self.chunk_size).chunk(preamble)
            )

        for index, match in enumerate(matches):
            heading = match.group().strip()
            section_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )
            body = text[match.end():section_end].strip()
            section = f"{heading}\n{body}".strip()

            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            available_size = max(1, self.chunk_size - len(heading) - 1)
            body_chunks = RecursiveChunker(chunk_size=available_size).chunk(body)

            for body_chunk in body_chunks:
                chunks.append(f"{heading}\n{body_chunk}".strip())

        return chunks
```

**Thành viên 2 — Trần Long Khánh**
- **Loại chiến lược:** RecursiveChunker, `chunk_size=500`.
- **Mô tả & lý do chọn:** Văn bản hành chính có điều, khoản và các dòng mốc thời gian, nên RecursiveChunker ưu tiên tách theo `\n\n`, `\n`, `. `, khoảng trắng rồi mới cắt ký tự. Cách này cố gắng giữ các ý trọn vẹn trước khi giảm kích thước chunk, phù hợp hơn với quy định có cấu trúc.
- **Code snippet (nếu custom):** Không áp dụng

**Thành viên 3 — Phạm Hồ Quang Dũng**
- **Loại chiến lược:** FixedSizeChunker, `chunk_size=500`, `overlap=50`.
- **Mô tả & lý do chọn:** Chọn FixedSizeChunker có overlap làm baseline vì dễ kiểm soát độ dài chunk và overlap giảm nguy cơ cắt mất thông tin ngay tại ranh giới. Chạy `bench.py` trên `data/registration/` (138 chunk) với embedding thật `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`, không phải MockEmbedder): cả 5/5 câu đều có chunk chứa đúng đáp án lọt vào top-3 (rank 2 hoặc rank 3), nhưng **0/5 câu đúng ở top-1** — chunk mở đầu/tiêu đề của mỗi tài liệu (đúng chủ đề, không có số liệu cụ thể) luôn thắng điểm cosine trước chunk thật sự chứa đáp án. Vì cắt cứng theo ký tự không tôn trọng câu/điều khoản, đáp án hay bị tách sang chunk kế tiếp thay vì nằm chung với phần mở đầu có similarity cao. Điểm rubric cá nhân: 5/10. Chi tiết: `ket_qua_benchmark.txt`, `report/REPORT_CANHAN.md` mục 5.
- **Code snippet (nếu custom):** Không áp dụng

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Đình Khang | HeadingAwareChunker, `chunk_size=700` | 7/10 | Dùng embedding multilingual thật; evidence ở top-1 cho Q1–Q3, top-2 cho Q5. Giữ heading với section làm mốc thời gian còn đủ ngữ cảnh. | Bỏ lỡ chunk học phí UEH ở Q4; 209 chunks cho 6 trang cho thấy menu/nhiễu vẫn ảnh hưởng xếp hạng. |
| Trần Long Khánh | RecursiveChunker, `chunk_size=500` | 3/10 | Chạy chuẩn hoá với embedding multilingual thật, có evidence ở Q1 và Q3 (top-2), Q5 (top-3); ưu tiên đoạn/dòng/câu phù hợp văn bản quy định. | Chưa lấy được evidence Q2, Q4; recursive không giữ heading nên các chunk chứa lịch dễ xếp sau phần tiêu đề/menu cùng trang. |
| Phạm Hồ Quang Dũng | FixedSizeChunker, `chunk_size=500`, `overlap=50` | 5/10 | Dùng embedding multilingual thật; đáp án lọt top-3 ở cả 5/5 câu — riêng Q2 và Q5 trúng đúng chunk gold chuẩn của nhóm (`ueh-quy-dinh...#12`, `ftu-dieu-chinh...#0`) ở rank 2. Độ dài chunk ổn định, overlap 50 hạn chế mất thông tin ở ranh giới. | Không câu nào đúng ở top-1 (0/5): cắt cứng theo ký tự tách đáp án ra khỏi đoạn mở đầu có similarity chủ đề cao, nên chunk đầu luôn thắng dù thiếu số liệu; 2/5 câu (Q2, Q5) bị chunk sai tài liệu (nhưng cùng chủ đề) chiếm top-1. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với bằng chứng kiểm tra trực tiếp trên embedding thật (cả 3 thành viên), HeadingAwareChunker hiện tốt nhất: đạt 7/10 và đưa mốc trả lời lên top-1 ở Q1–Q3, vì giữ nguyên heading giúp mỗi chunk có đặc trưng riêng thay vì chỉ là đoạn mở đầu chung chung. Recursive đạt 3/10: giữ được câu trọn vẹn nhưng không neo theo heading nên vẫn bị lẫn với phần mở đầu/tiêu đề. FixedSize đạt 5/10 — luôn đưa được đáp án vào top-3 (5/5) nhờ overlap, nhưng chưa bao giờ đứng top-1 vì cắt cứng theo ký tự tách rời đáp án khỏi đoạn có similarity chủ đề cao nhất. Xu hướng chung: **chunk nào giữ được cấu trúc ngữ nghĩa của văn bản quy định (heading/điều khoản) thắng chunk chỉ kiểm soát độ dài**.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Query | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | 23/08/2026, 09:00–16:00 | `uit-dieu-chinh...#0` |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | Trước ngày thi kết thúc học phần 10 ngày | `ueh-quy-dinh...#12` |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | 14/09–18/09/2026; mỗi ngày 09:00–22:00 | `ftu-thoi-khoa-bieu...#0` |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | 1.650.000 VNĐ/tín chỉ | `ueh-dang-ky...#1` |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | 05/08–14/08/2026 | `ftu-dieu-chinh...#0` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0). Cột "Có chunk liên quan trong top-3?" tính theo **chiến lược tốt nhất** cho câu đó (best-of-3), vì nhóm được tính điểm khi ít nhất một chiến lược trong nhóm giải được câu hỏi.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú (cả 3 chiến lược) |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | UIT khóa 20 đăng ký HK1 2026–2027 khi nào? | Heading-aware | Có — top-1 (2đ) | Heading-aware: top-1. Recursive: top-2. FixedSize: top-3 (`uit-dieu-chinh...#1`, chứa đúng "23/08/2026...khóa 20"). |
| 2 | UEH hủy học phần đã đóng học phí và không rút học phí trước hạn nào? | Heading-aware | Có — top-1 (2đ) | Heading-aware lấy đúng `ueh-...#16`, chứa "trước ngày thi kết thúc ... 10 ngày". FixedSize: top-2, trúng đúng chunk gold `ueh-quy-dinh...#12`. Recursive: chưa có evidence trong top-3. |
| 3 | FTU K63/K64 đăng ký tín chỉ bổ sung khi nào? | Heading-aware | Có — top-1 (2đ) | Heading-aware: top-1. Recursive: top-2. FixedSize: top-3 (`ftu-thoi-khoa-bieu...#1`, chứa đúng "14/9/2026 đến 18/9/2026, K63, K64"). |
| 4 | Học phí học phần thạc sĩ cho sinh viên đại học UEH là bao nhiêu? | FixedSize | Có — top-2 (1đ) | FixedSize là chiến lược **duy nhất** có evidence: `ueh-dang-ky-hoc-phan-thac-si-dot1-2026#8` chứa đúng "Mức học phí: 1.650.000 VNĐ/tín chỉ" ở rank 2. Heading-aware và Recursive chưa tìm được chunk chứa số liệu này trong top-3. |
| 5 | FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào? | Heading-aware / FixedSize (đồng hạng) | Có — top-2 (1đ) | Heading-aware: top-2 (`ftu-dieu-chinh-...#24`). FixedSize: top-2, trúng đúng chunk gold `ftu-dieu-chinh...#0`. Recursive: top-3. |

**Điểm retrieval theo rubric (best-of-3 mỗi câu): 2+2+2+1+1 = 8/10.**

**Lưu ý về tính công bằng của so sánh:** Cả 3 thành viên đã chạy lại bằng cùng một embedding backend thật `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` trên cùng corpus `data/registration/` và cùng 5 query — không còn thành viên nào dùng `MockEmbedder`. Chấm theo evidence nội dung (chuỗi đặc trưng của gold answer có thật trong chunk), không chỉ dựa vào `doc_id` đúng/sai, đúng tinh thần "chấm 2 mức" của lab. Vì chưa có output agent/LLM thật (đang dùng hàm LLM giả lập), đây là điểm retrieval-evidence, chưa phải điểm cuối cùng có tính cả bước sinh câu trả lời.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Với FixedSizeChunker (Dũng), chạy A/B cả 5 câu — có và không có `metadata_filter={"audience":"student"}` — cho **kết quả giống hệt nhau ở cả 5/5 câu**: tài liệu `ftu-quy-che-dao-tao-tin-chi` (`audience=all`) không lọt top-3 dù không lọc, vì đây là văn bản dài (46KB), chunk theo ký tự cố định làm loãng nội dung nên độ tương đồng cosine với các câu hỏi cụ thể luôn thấp hơn các thông báo ngắn cùng chủ đề. Với chiến lược và bộ 5 câu hiện tại, filter `audience` **chưa chứng minh được tác dụng thực nghiệm** — đúng cảnh báo của lab "kết quả giống hệt nhau nghĩa là câu hỏi chưa thực sự cần filter". Nhóm cần thử lại A/B này với HeadingAwareChunker (dễ giữ nguyên đoạn dài của quy chế thành chunk mạch lạc hơn, có thể đủ sức lọt top-3 và khiến filter phát huy tác dụng) trước khi kết luận field `audience` không cần thiết, hoặc bổ sung tài liệu `staff` thật để tạo cạnh tranh rõ ràng hơn cho filter.

### Failure case — Câu 5 "FTU điều chỉnh lịch đăng ký cho khóa 60–64 thành thời gian nào?" (FixedSizeChunker)

- **Câu nào hỏng:** Top-1 (score 0,7806) trả về `ftu-thoi-khoa-bieu-lich-dang-ky-tin-chi-k65#0` — **sai tài liệu**: đây là thông báo TKB K65 và đăng ký bổ sung, không phải thông báo điều chỉnh lịch cho khóa 60–64. Đáp án đúng (`05/08–14/08/2026`) nằm ở `ftu-dieu-chinh-thoi-gian-dang-ky-hoc-tap#0`, chỉ xếp rank 2 (score 0,7492) — chênh lệch rất nhỏ (0,03).
- **Vì sao:** Hai tài liệu đều là thông báo FTU về "đăng ký tín chỉ/học tập", chia sẻ gần như toàn bộ từ vựng chủ đề (khóa, đăng ký, tín chỉ, thời gian), nên cosine similarity giữa chúng và câu hỏi gần bằng nhau dù nội dung cụ thể khác hẳn (một cái nói khóa 65, cái kia nói khóa 60–64). Chunk `#0` của cả hai tài liệu đều là đoạn mở đầu chung chung, không đủ đặc trưng để phân biệt — cosine đo độ giống chủ đề chứ không đo đúng/sai về đối tượng áp dụng.
- **Đề xuất sửa:** (1) Thêm số khóa (60–64 / K65) vào câu hỏi benchmark để giảm ambiguity từ vựng; (2) dùng HeadingAwareChunker để chunk mở đầu ngắn gọn hơn, ít lẫn nội dung chung; (3) cân nhắc thêm metadata `applies_to_cohort` (khóa áp dụng) để lọc trực tiếp thay vì chỉ dựa vào embedding.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Tách theo heading đưa các mốc thời gian/quy định quan trọng lên top-1 ở Q1–Q3, tốt hơn FixedSize và Recursive khi đo trên cùng embedding thật.
> - Chỉ đúng `doc_id` chưa đủ: cả 3 chiến lược đều từng bị chunk mở đầu (đúng chủ đề, không có số liệu) chiếm top-1 thay vì chunk chứa đáp án thật — nhóm chấm theo evidence ở cấp nội dung chunk thay vì chỉ xem đúng tài liệu.
> - FixedSizeChunker cho thấy rõ nhất giới hạn của cosine similarity: đáp án luôn lọt top-3 (5/5, nhờ overlap) nhưng không bao giờ đứng top-1, vì đoạn mở đầu/tiêu đề luôn thắng về độ giống chủ đề dù thiếu số liệu cụ thể — cosine đo chủ đề, không đo mật độ thông tin trả lời được.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus, cùng một embedding backend, chiến lược chunking quyết định thông tin nào được giữ chung với tiêu đề/ngữ cảnh và được đưa vào kết quả truy xuất. Heading-aware phù hợp nhất với văn bản quy định vì không cắt rời điều/mục và giữ mỗi chunk đủ đặc trưng riêng. Recursive giữ được câu trọn vẹn nhưng vẫn có thể lẫn với phần mở đầu do không neo theo heading. FixedSize hữu ích như baseline đơn giản, dễ kiểm soát độ dài, nhưng luôn thua ở vị trí top-1 vì tách đáp án ra khỏi đoạn có similarity chủ đề cao nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ làm sạch menu, footer và danh sách liên kết lặp lại trước khi chunk để giảm số chunk nhiễu. Đồng thời, nhóm sẽ bổ sung tài liệu công khai cho audience `staff` và thiết kế lại câu A/B để metadata filter thực sự thay đổi kết quả (hiện tại `audience=all` tự nhiên không lọt top-3 nên filter chưa chứng minh được tác dụng). Cuối cùng, mọi thành viên đã thống nhất chạy cùng embedding backend thật, cùng 5 query và lưu evidence extract để việc so sánh tái lập được — cần giữ kỷ luật này cho các lần benchmark sau.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 8 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 *(best-of-3 mỗi câu: 2+2+2+1+1, sau khi cập nhật evidence đúng của FixedSizeChunker ở Q2, Q4, Q5)* |
| Thuyết trình (Demo) | 0 / 5 *(chưa thuyết trình trực tiếp)* |
| **Tổng phần nhóm** | **29 / 40** |
