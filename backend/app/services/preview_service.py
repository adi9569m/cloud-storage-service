import os
import re
from typing import Optional, Tuple
import uuid
from fastapi import HTTPException, Response, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.share import Share
from app.schemas.preview import TextContentResponse
from app.services.storage_service import StorageService

class PreviewService:
    """Service providing inline preview streaming with HTTP Range support and text decoding."""

    TEXT_MIME_PATTERNS = [
        r"^text/",
        r"^application/json",
        r"^application/javascript",
        r"^application/typescript",
        r"^application/xml",
        r"^application/x-yaml",
        r"^application/sql",
    ]

    TEXT_EXTENSIONS = {
        "txt", "md", "markdown", "py", "js", "jsx", "ts", "tsx", "html", "htm", "css", "scss",
        "json", "xml", "yaml", "yml", "csv", "tsv", "sql", "sh", "bash", "ps1", "c", "cpp",
        "h", "hpp", "java", "rs", "go", "php", "rb", "env", "dockerfile", "toml", "ini", "log"
    }

    @classmethod
    def _verify_file_access(cls, db: Session, file_id: uuid.UUID, user_id: uuid.UUID) -> File:
        """Verify user has owner or share access to the file."""
        file = db.scalars(
            select(File).where(File.id == file_id, File.is_deleted.is_(False))
        ).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )

        if file.owner_id == user_id:
            return file

        share = db.scalars(
            select(Share).where(
                Share.grantee_id == user_id,
                (Share.file_id == file_id) | (Share.folder_id == file.folder_id),
            )
        ).first()

        if not share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this file.",
            )

        return file

    @classmethod
    def get_file_preview_response(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        range_header: Optional[str] = None,
    ) -> Response:
        """Generate inline preview response supporting HTTP 206 Partial Content Range streaming."""
        file = cls._verify_file_access(db=db, file_id=file_id, user_id=user_id)
        data = StorageService.get_file_bytes(file.storage_path)

        if data is None:
            data = b""

        total_size = len(data)
        safe_filename = StorageService.sanitize_filename(file.name)
        mime_type = file.mime_type or "application/octet-stream"

        if range_header and range_header.startswith("bytes="):
            range_spec = range_header[6:].strip()
            parts = range_spec.split("-")
            start_str, end_str = parts[0], parts[1] if len(parts) > 1 else ""

            try:
                if start_str and end_str:
                    start = int(start_str)
                    end = min(int(end_str), total_size - 1)
                elif start_str:
                    start = int(start_str)
                    end = total_size - 1
                elif end_str:

                    start = max(0, total_size - int(end_str))
                    end = total_size - 1
                else:
                    start = 0
                    end = total_size - 1
            except ValueError:
                start = 0
                end = total_size - 1

            if start >= total_size or start < 0 or end < start:
                return Response(
                    status_code=getattr(status, "HTTP_416_RANGE_NOT_SATISFIABLE", 416),
                    headers={"Content-Range": f"bytes */{total_size}"},
                )

            chunk = data[start : end + 1]
            chunk_length = len(chunk)

            headers = {
                "Content-Range": f"bytes {start}-{end}/{total_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_length),
                "Content-Type": mime_type,
                "Content-Disposition": f'inline; filename="{safe_filename}"',
            }

            return Response(
                content=chunk,
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                headers=headers,
                media_type=mime_type,
            )

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(total_size),
            "Content-Type": mime_type,
            "Content-Disposition": f'inline; filename="{safe_filename}"',
        }

        return Response(
            content=data,
            status_code=status.HTTP_200_OK,
            headers=headers,
            media_type=mime_type,
        )

    @classmethod
    def get_text_content(
        cls,
        db: Session,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TextContentResponse:
        """Read and decode text/code content for in-browser viewing or code editor inspection."""
        file = cls._verify_file_access(db=db, file_id=file_id, user_id=user_id)

        ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
        is_text_ext = ext in cls.TEXT_EXTENSIONS
        is_text_mime = any(re.search(pat, file.mime_type or "") for pat in cls.TEXT_MIME_PATTERNS)

        if not is_text_ext and not is_text_mime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.name}' is not a text or code document.",
            )

        raw_bytes = StorageService.get_file_bytes(file.storage_path) or b""

        is_truncated = False
        if len(raw_bytes) > settings.MAX_PREVIEW_TEXT_BYTES:
            raw_bytes = raw_bytes[: settings.MAX_PREVIEW_TEXT_BYTES]
            is_truncated = True

        try:
            text = raw_bytes.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("latin-1")
                encoding = "latin-1"
            except Exception:
                text = raw_bytes.decode("utf-8", errors="replace")
                encoding = "utf-8 (lossy)"

        lines = text.splitlines()

        return TextContentResponse(
            id=file.id,
            name=file.name,
            mime_type=file.mime_type,
            size_bytes=file.size_bytes,
            encoding=encoding,
            content=text,
            line_count=len(lines),
            is_truncated=is_truncated,
        )
