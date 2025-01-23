from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.email_service import EmailService, AuthError

router = APIRouter()

@router.get("/otp")
async def get_otp(
    email: str,
    password: str,
    client_id: str,
    refresh_token: str,
    folders: Optional[List[str]] = Query(None)
):
    try:
        email_service = EmailService(email, password, client_id, refresh_token)
        return await email_service.get_otp_from_emails(folders)
    except AuthError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "correlation_id": e.correlation_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/otp/string")
async def get_otp_from_string(
    hotmail_str: str,
    folders: Optional[List[str]] = Query(None)
):
    try:
        email, password, refresh_token, client_id = hotmail_str.split('|')
        email_service = EmailService(email, password, client_id, refresh_token)
        return await email_service.get_otp_from_emails(folders)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail={
                "error_code": "invalid_format",
                "message": "Chuỗi không đúng định dạng. Yêu cầu: email|password|refresh_token|client_id"
            }
        )
    except AuthError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "correlation_id": e.correlation_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_emails(
    email: str,
    password: str,
    client_id: str,
    refresh_token: str,
    query: str,
    folders: Optional[List[str]] = Query(None)
):
    try:
        email_service = EmailService(email, password, client_id, refresh_token)
        return await email_service.search_emails(query, folders)
    except AuthError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "correlation_id": e.correlation_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 