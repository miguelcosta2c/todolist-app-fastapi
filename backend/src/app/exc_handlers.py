from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.main import app, logger

# Global Errors Handler


@app.exception_handler(Exception)
async def erro_global_handler(request: Request, exc: Exception) -> JSONResponse:
    # Loga o erro REAL no painel do Render para VOCÊ ver
    logger.critical(
        "Erro não tratado na rota %s: %s",
        request.url.path,
        exc,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "Ocorreu um erro inesperado. Já fomos notificados.",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def global_db_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error("Erro de Banco de Dados: %s", exc)
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": "DatabaseError",
            "message": (
                "Serviço temporariamente indisponível. Tente novamente em instantes."
            ),
        },
    )
