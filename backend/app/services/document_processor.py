import os
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from pptx import Presentation

from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store


class DocumentProcessor:
    """
    Document processing utility for parsing PDF documents and PPT PowerPoint presentations.
    Extracts text page-by-page or slide-by-slide, chunks text with overlapping windows,
    tags metadata (doc_type, page_number or slide_number), generates vector embeddings,
    and upserts into vector store.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text_with_overlap(self, text: str) -> List[str]:
        """
        Splits text into chunks of `chunk_size` characters with `overlap` characters overlap.
        """
        clean_text = text.strip()
        if not clean_text:
            return []
        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks = []
        start = 0
        step = self.chunk_size - self.overlap
        if step <= 0:
            step = self.chunk_size

        while start < len(clean_text):
            end = start + self.chunk_size
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += step

        return chunks

    def extract_pdf_pages(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF page-by-page using pypdf.
        Returns list of pages: [{"page_number": 1, "text": "..."}, ...]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        reader = PdfReader(file_path)
        pages_data = []

        for idx, page in enumerate(reader.pages):
            page_number = idx + 1
            extracted_text = page.extract_text() or ""
            if extracted_text.strip():
                pages_data.append(
                    {
                        "page_number": page_number,
                        "text": extracted_text.strip(),
                    }
                )

        return pages_data

    def extract_ppt_slides(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PPT PowerPoint slides slide-by-slide using python-pptx.
        Returns list of slides: [{"slide_number": 1, "text": "..."}, ...]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PPT file not found at: {file_path}")

        prs = Presentation(file_path)
        slides_data = []

        for idx, slide in enumerate(prs.slides):
            slide_number = idx + 1
            slide_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_texts.append(shape.text.strip())

            full_slide_text = "\n".join(slide_texts).strip()
            if full_slide_text:
                slides_data.append(
                    {
                        "slide_number": slide_number,
                        "text": full_slide_text,
                    }
                )

        return slides_data

    def process_and_ingest_pdf(
        self,
        file_path: str,
        doc_id: str,
        title: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parses PDF, chunks text page-by-page with overlap, tags metadata, generates embeddings,
        and upserts into vector store.
        """
        pages = self.extract_pdf_pages(file_path)
        formatted_pages = []

        for pg in pages:
            page_number = pg["page_number"]
            page_text = pg["text"]
            text_chunks = self.chunk_text_with_overlap(page_text)

            for chunk_sub_idx, chunk in enumerate(text_chunks):
                formatted_pages.append(
                    {
                        "page_number": page_number,
                        "text": chunk,
                        "sub_index": chunk_sub_idx,
                    }
                )

        # Upsert into vector store using add_pdf_pages
        vector_store.add_pdf_pages(
            doc_id=doc_id,
            title=title,
            pages=formatted_pages,
            course_id=course_id,
        )

        return {
            "doc_id": doc_id,
            "title": title,
            "doc_type": "pdf",
            "total_pages_extracted": len(pages),
            "total_chunks_upserted": len(formatted_pages),
        }

    def process_and_ingest_ppt(
        self,
        file_path: str,
        doc_id: str,
        title: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parses PPT, chunks text slide-by-slide with overlap, tags metadata, generates embeddings,
        and upserts into vector store.
        """
        slides = self.extract_ppt_slides(file_path)
        formatted_slides = []

        for sld in slides:
            slide_number = sld["slide_number"]
            slide_text = sld["text"]
            text_chunks = self.chunk_text_with_overlap(slide_text)

            for chunk_sub_idx, chunk in enumerate(text_chunks):
                formatted_slides.append(
                    {
                        "slide_index": slide_number,
                        "text": chunk,
                        "sub_index": chunk_sub_idx,
                    }
                )

        # Upsert into vector store using add_ppt_slides
        vector_store.add_ppt_slides(
            doc_id=doc_id,
            title=title,
            slides=formatted_slides,
            course_id=course_id,
        )

        return {
            "doc_id": doc_id,
            "title": title,
            "doc_type": "ppt",
            "total_slides_extracted": len(slides),
            "total_chunks_upserted": len(formatted_slides),
        }


document_processor = DocumentProcessor()
