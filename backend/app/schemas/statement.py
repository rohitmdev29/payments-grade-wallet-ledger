from pydantic import BaseModel


class StatementEntry(BaseModel):
    id: int
    transfer_id: int
    direction: str
    amount_paise: int
    created_at: str


class StatementResponse(BaseModel):
    entries: list[StatementEntry]
    next_cursor: str | None = None


class StatementQuestion(BaseModel):
    question: str


class StatementAnswer(BaseModel):
    total_paise: int | None = None
    count: int | None = None
    transfer_ids: list[int] = []
