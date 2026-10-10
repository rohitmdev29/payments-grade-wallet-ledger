from pydantic import BaseModel


class TransferCreate(BaseModel):
    type: str                            # TOP_UP | PEER | WITHDRAWAL
    from_account_id: int | None = None
    to_account_id: int | None = None
    amount: int                          # paise


class TransferResponse(BaseModel):
    transfer_id: int
    status: str
