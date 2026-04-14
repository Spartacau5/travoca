import re
from typing import Optional

from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    LLMMessagesFrame,
    LLMFullResponseEndFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from prompts.sensei import build_system_prompt
from services.supabase_client import SupabaseClient
from processors.gamification import GamificationEngine

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
LESSON_COMPLETE_PATTERN = re.compile(r"LESSON_COMPLETE:\s*(\{.*?\})", re.DOTALL)


class TeachingBrainProcessor(FrameProcessor):
    def __init__(self, lesson_manager, override_lesson_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.lesson_manager = lesson_manager
        self._override_lesson_id = override_lesson_id
        self.db = SupabaseClient()
        self.gamification = GamificationEngine()
        self.conversation_history: list[dict] = []
        self.current_lesson: dict | None = None
        self.user_progress: dict | None = None
        self.session_id: str | None = None
        self.session_data = {
            "turn_count": 0,
            "vocab_used": [],
            "pronunciation_scores": [],
        }

    async def start_lesson(self):
        """Called when learner connects. Load state and begin."""
        self.user_progress = await self.db.get_user_progress(DEV_USER_ID)
        current_lesson_id = self._override_lesson_id or await self.db.get_current_lesson_id(DEV_USER_ID)
        self.current_lesson = self.lesson_manager.load_lesson(current_lesson_id)
        self.session_id = await self.db.create_session(DEV_USER_ID, current_lesson_id)
        self.conversation_history = []

        print(f"[TeachingBrain] Starting lesson: {self.current_lesson['title']}")

        # Trigger Claude to send the opening greeting
        self.conversation_history.append({
            "role": "user",
            "content": (
                "[SYSTEM: The student just joined. Say hi in 1 sentence and ask them to greet you in Japanese. Nothing more.]"
            ),
        })
        await self._emit_messages()

    async def end_session(self):
        """Called when learner disconnects. Save everything."""
        if self.session_id:
            await self.db.finalize_session(
                session_id=self.session_id,
                turn_count=self.session_data["turn_count"],
                avg_pronunciation=self._avg_pronunciation(),
                transcript=self.conversation_history,
            )
            await self.gamification.update_streak(DEV_USER_ID, self.db)

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            user_text = frame.text
            if not user_text or not user_text.strip():
                return

            self.session_data["turn_count"] += 1

            # If the last entry in history is also a user message (bot was interrupted
            # before finishing its response, so ResponseRecorder never added an assistant
            # turn), REPLACE it with the newer message instead of appending.
            # This prevents consecutive user messages from confusing Claude and ensures
            # the bot only responds to the learner's latest utterance.
            if (
                self.conversation_history
                and self.conversation_history[-1].get("role") == "user"
            ):
                self.conversation_history[-1] = {"role": "user", "content": user_text}
            else:
                self.conversation_history.append({"role": "user", "content": user_text})

            self._check_vocab_usage(user_text)
            await self._emit_messages()

        else:
            await self.push_frame(frame, direction)

    async def _emit_messages(self):
        """Build messages array and push LLMMessagesFrame downstream."""
        if not self.current_lesson or not self.user_progress:
            return

        system_prompt = build_system_prompt(
            lesson=self.current_lesson,
            progress=self.user_progress,
            session_data=self.session_data,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
        ]

        await self.push_frame(LLMMessagesFrame(messages))

    def _check_vocab_usage(self, text: str):
        if not self.current_lesson:
            return
        for vocab in self.current_lesson.get("vocabulary", []):
            word = vocab["word"]
            reading = vocab["reading"]
            if (word in text or reading in text) and word not in self.session_data["vocab_used"]:
                self.session_data["vocab_used"].append(word)

    def _avg_pronunciation(self) -> Optional[float]:
        scores = self.session_data["pronunciation_scores"]
        return sum(scores) / len(scores) if scores else None

    def record_assistant_response(self, text: str):
        """Called by ResponseRecorder after LLM response completes."""
        if text.strip():
            self.conversation_history.append({"role": "assistant", "content": text.strip()})


class ResponseRecorder(FrameProcessor):
    """Sits between LLM and TTS. Accumulates text chunks and records the
    complete assistant response back to TeachingBrainProcessor when done."""

    def __init__(self, teaching_brain: "TeachingBrainProcessor", **kwargs):
        super().__init__(**kwargs)
        self._brain = teaching_brain
        self._buffer: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TextFrame):
            self._buffer.append(frame.text)
        elif isinstance(frame, LLMFullResponseEndFrame):
            full_text = "".join(self._buffer).strip()
            if full_text:
                self._brain.record_assistant_response(full_text)
                print(f"[Yuki] {full_text}")
            self._buffer = []

        await self.push_frame(frame, direction)
