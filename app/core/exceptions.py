from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

def create_error_response(code: str, message: str, field_errors: list = None, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "field_errors": field_errors or [],
            }
        },
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    code = f"HTTP_{exc.status_code}"
    return create_error_response(code=code, message=str(exc.detail), status_code=exc.status_code)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = []
    for err in exc.errors():
        field_errors.append({
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "issue": err.get("msg", "Invalid value"),
        })
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request payload validation failed",
        field_errors=field_errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    import traceback
    traceback.print_exc()
    if isinstance(exc, IntegrityError):
        return create_error_response(
            code="DATABASE_INTEGRITY_ERROR",
            message="Database constraint or integrity violation",
            status_code=status.HTTP_409_CONFLICT,
        )
    return create_error_response(
        code="DATABASE_ERROR",
        message=f"An unexpected database error occurred: {str(exc)}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message=f"An unexpected internal server error occurred: {str(exc)}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
