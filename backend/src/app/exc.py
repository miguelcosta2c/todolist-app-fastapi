class InvalidCredentialsError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserAlreadyDeletedError(Exception):
    pass


class InvalidTokenError(Exception):
    def __init__(self, msg: str) -> None:
        self.mensagem = msg
        super().__init__(self.mensagem)
