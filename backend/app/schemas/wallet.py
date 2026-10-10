from pydantic import BaseModel


class WalletCreate(BaseModel):
    user_id: int
    name: str


class WalletResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    name: str
    currency: str


class BalanceResponse(BaseModel):
    account_id: int
    balance_paise: int
    currency: str
