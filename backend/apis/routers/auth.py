from fastapi import APIRouter, Depends, Request, Response

from apis.dependencies import get_auth_service, get_current_user
from services.auth_service import AbstractAuthService
from schemas.user import LoginRequest, RegisterRequest

router = APIRouter()


@router.post("/register")
async def register(
    response: Response,
    body: RegisterRequest,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    user, session_id = await auth_service.register(body)
    response.set_cookie("session_id", session_id, httponly=True)
    return user


@router.post("/login")
async def login(
    response: Response,
    body: LoginRequest,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    user, session_id = await auth_service.login(body)
    response.set_cookie("session_id", session_id, httponly=True)
    return user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: AbstractAuthService = Depends(get_auth_service),
):
    session_id = request.cookies.get("session_id")
    if session_id:
        await auth_service.logout(session_id)
    response.delete_cookie("session_id")
    response.delete_cookie("chat_session_id")
    return {"message": "logged out"}
