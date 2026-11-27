class TutorError(Exception):
    """A failure the frontend should show to the student as is."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
