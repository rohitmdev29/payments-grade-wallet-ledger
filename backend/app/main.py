from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.errors import WalletError
from app.api.v1 import users, wallets, transfers, statements, admin

app = FastAPI(
    title="Payments-Grade Wallet Ledger",
    description="Double-entry ledger backend for a digital wallet.",
    version="1.0.0",
)

app.include_router(users.router,      prefix="/api/v1/users",      tags=["users"])
app.include_router(wallets.router,    prefix="/api/v1/wallets",    tags=["wallets"])
app.include_router(transfers.router,  prefix="/api/v1/transfers",  tags=["transfers"])
app.include_router(statements.router, prefix="/api/v1",            tags=["statements"])
app.include_router(admin.router,      prefix="/api/v1/admin",      tags=["admin"])


@app.exception_handler(WalletError)
async def wallet_error_handler(request: Request, exc: WalletError):
    """Return one consistent JSON error shape for all wallet errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": request.headers.get("x-request-id", ""),
        },
    )


@app.get("/health")
async def health():
    """Liveness endpoint for docker compose."""
    return {"status": "ok"}
