from curriculum.lessons import get_lesson, get_next_incomplete_lesson, get_all_lessons


class LessonManager:
    """Manages lesson state and curriculum position."""

    def __init__(self):
        self.current_lesson: dict | None = None
        self.current_lesson_id: str | None = None

    def load_lesson(self, lesson_id: str) -> dict:
        self.current_lesson = get_lesson(lesson_id)
        self.current_lesson_id = lesson_id
        return self.current_lesson

    def get_current_lesson(self) -> dict | None:
        return self.current_lesson

    def get_next_lesson(self, completed_ids: list[str]) -> dict:
        return get_next_incomplete_lesson(completed_ids)

    def get_all_lessons(self) -> list:
        return get_all_lessons()
