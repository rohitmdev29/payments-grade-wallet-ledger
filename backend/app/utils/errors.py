class WalletError(Exception):
    """Base class for all wallet-related errors."""

    code = "WALLET_ERROR"
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InsufficientFunds(WalletError):
    code = "INSUFFICIENT_FUNDS"
    status_code = 422

    def __init__(self, account_id: int, balance: int, required: int):
        super().__init__(
            f"Account {account_id} has {balance} paise, "
            f"but {required} paise required"
        )


class AccountNotFound(WalletError):
    code = "ACCOUNT_NOT_FOUND"
    status_code = 404

    def __init__(self, account_id: int):
        super().__init__(f"Account {account_id} not found")


class IdempotencyConflict(WalletError):
    code = "IDEMPOTENCY_CONFLICT"
    status_code = 422

    def __init__(self):
        super().__init__("Same idempotency key used with a different body")


class RequestInProgress(WalletError):
    code = "REQUEST_IN_PROGRESS"
    status_code = 409

    def __init__(self):
        super().__init__("A request with this idempotency key is in progress")


class InvalidAmount(WalletError):
    code = "INVALID_AMOUNT"
    status_code = 400

    def __init__(self):
        super().__init__("Amount must be a positive integer")


class SelfTransfer(WalletError):
    code = "SELF_TRANSFER"
    status_code = 400

    def __init__(self):
        super().__init__("Cannot transfer to the same account")
