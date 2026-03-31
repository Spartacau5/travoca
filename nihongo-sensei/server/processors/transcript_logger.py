from pipecat.frames.frames import Frame, TranscriptionFrame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor


class TranscriptLogger(FrameProcessor):
    """Logs conversation turns. Passes all frames through unchanged."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def process_frame(self, frame: Frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            print(f"[Learner] {frame.text}")
        elif isinstance(frame, TextFrame):
            print(f"[Yuki] {frame.text}")

        await self.push_frame(frame, direction)
