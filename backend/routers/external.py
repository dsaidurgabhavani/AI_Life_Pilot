from typing import Optional, List
from fastapi import APIRouter, Query, UploadFile, File, Response, HTTPException
from external_services import (
    get_live_weather,
    search_web,
    get_current_time,
    parse_uploaded_document,
    generate_icalendar
)
from database import get_connection, save_user_document
from models import (
    WeatherResponse,
    WebSearchResponse,
    DocumentUploadResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse
)

router = APIRouter(prefix="/api/external", tags=["Real-Time External Integrations"])

@router.get("/weather", response_model=WeatherResponse)
def get_weather_endpoint(location: str = Query("Vijayawada")):
    result = get_live_weather(location)
    return WeatherResponse(**result)

@router.get("/search", response_model=WebSearchResponse)
def web_search_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=10)
):
    result = search_web(q, max_results=limit)
    return WebSearchResponse(**result)

@router.get("/time")
def get_time_endpoint(tz: str = Query("auto")):
    return get_current_time(timezone_name=tz)

@router.post("/upload-doc", response_model=DocumentUploadResponse)
async def upload_document_endpoint(file: UploadFile = File(...)):
    try:
        content = await file.read()
        parsed = parse_uploaded_document(file.filename or "uploaded_doc.txt", content)
        raw_text = parsed["text"]

        # Simple initial extraction / summary
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        preview = " ".join(lines[:3]) if lines else "Document uploaded."
        summary = f"Parsed {parsed['word_count']} words. Preview: {preview[:200]}..."

        doc_record = save_user_document(
            filename=parsed["filename"],
            content=raw_text,
            summary=summary
        )

        return DocumentUploadResponse(
            id=doc_record["id"],
            filename=doc_record["filename"],
            char_count=parsed["char_count"],
            word_count=parsed["word_count"],
            summary=summary,
            created_at=doc_record["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process document: {str(e)}")

@router.get("/calendar.ics")
def export_calendar_ics():
    """
    Exports the user's tasks to an RFC 5545 standard .ics file
    compatible with Google Calendar, Outlook, and Apple Calendar.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
    tasks = [dict(r) for r in cursor.fetchall()]
    conn.close()

    ics_content = generate_icalendar(tasks)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=lifepilot_schedule.ics"
        }
    )
