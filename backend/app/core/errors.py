from fastapi import HTTPException, status
from typing import Any, Optional, Dict


class AppError(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
        code: str = "APP_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail={"message": detail, "code": code, "extra": extra or {}})


class AuthenticationError(AppError):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, code="AUTH_ERROR")


class PermissionDeniedError(AppError):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, code="PERMISSION_DENIED")


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource", identifier: Any = ""):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} {identifier} not found".strip(),
            code="NOT_FOUND",
        )


class QuotaExceededError(AppError):
    def __init__(self, detail: str = "Resource quota exceeded"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail, code="QUOTA_EXCEEDED")


class PromptInjectionDetectedError(AppError):
    def __init__(self, detail: str = "Potential prompt injection or security policy violation detected"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, code="PROMPT_INJECTION_DETECTED")
