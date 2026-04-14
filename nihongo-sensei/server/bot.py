"""
Nihongo Sensei - Pipecat voice pipeline
Run with: python bot.py
"""

import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCPatchRequest,
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)
from pipecat.transports.base_transport import TransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

from processors.teaching_brain import TeachingBrainProcessor, ResponseRecorder
from processors.lesson_manager import LessonManager
from processors.transcript_logger import TranscriptLogger
from curriculum.lessons import get_all_lessons, get_lesson
from config import settings

load_dotenv()

small_webrtc_handler = SmallWebRTCRequestHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()
    yield
    await small_webrtc_handler.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/lessons")
async def list_lessons():
    return JSONResponse(content=get_all_lessons())


@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, lesson_id: str | None = None):
    async def webrtc_connection_callback(connection: SmallWebRTCConnection):
        # Build everything synchronously here, BEFORE the HTTP response is sent.
        # This ensures event handlers are registered on the connection before
        # ICE completes (which can happen immediately after the response is sent).
        transport = SmallWebRTCTransport(
            webrtc_connection=connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(
                    params=VADParams(
                        confidence=0.6,
                        start_secs=0.15,
                        stop_secs=0.3,
                        min_volume=0.4,
                    )
                ),
            ),
        )

        lesson_manager = LessonManager()
        teaching_brain = TeachingBrainProcessor(lesson_manager=lesson_manager, override_lesson_id=lesson_id)
        response_recorder = ResponseRecorder(teaching_brain=teaching_brain)
        transcript_logger = TranscriptLogger()

        # task_ref lets the disconnect handler cancel the pipeline
        task_ref: list[PipelineTask] = []

        @transport.event_handler("on_client_connected")
        async def on_connected(_transport, _client):
            print("Learner connected! Starting lesson...")
            try:
                await teaching_brain.start_lesson()
            except Exception as e:
                import traceback
                print(f"[start_lesson ERROR] {e}")
                traceback.print_exc()

        @transport.event_handler("on_client_disconnected")
        async def on_disconnected(_transport, _client):
            print("Learner disconnected. Saving progress...")
            try:
                await teaching_brain.end_session()
            except Exception as e:
                print(f"[end_session ERROR] {e}")
            if task_ref:
                await task_ref[0].cancel()

        asyncio.create_task(
            run_pipeline(transport, teaching_brain, response_recorder, transcript_logger, task_ref, lesson_id)
        )

    answer = await small_webrtc_handler.handle_web_request(
        request=request,
        webrtc_connection_callback=webrtc_connection_callback,
    )
    return answer


@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    await small_webrtc_handler.handle_patch_request(request)
    return {"status": "ok"}


def _build_deepgram_keyterms(lesson_id: str | None) -> list[str]:
    """Build Deepgram keyterm list — focused on the selected lesson's vocab plus
    a small core of universally useful phrases. Deepgram caps keyterms at ~50,
    so we keep the list tight."""
    terms: list[str] = []

    # Lesson-specific romaji (highest priority)
    if lesson_id:
        try:
            lesson = get_lesson(lesson_id)
            for v in lesson.get("vocabulary", []):
                romaji = v.get("romaji", "").strip().lower()
                if romaji:
                    terms.append(romaji)
        except Exception:
            pass

    # Small universal core — most common greetings + connectives the learner
    # keeps using across lessons, plus phonetic variants for words commonly mis-heard.
    terms.extend([
        "konnichiwa", "konichi wa",
        "ohayou gozaimasu", "ohayou",
        "konbanwa", "sayounara", "sayonara",
        "genki desu ka", "genki desu", "genki",
        "arigatou gozaimasu", "arigatou",
        "sumimasen", "hai", "iie",
        "watashi wa", "desu", "desu ka",
        "onegaishimasu", "kudasai",
        "suki desu", "kirai desu", "daisuki desu",
        "ongaku", "on ga ku", "own ga ku",
        "tabemono", "ta be mo no",
        "eiga", "ay ga", "e ga",
        "oishii", "wakarimasen",
    ])

    # Dedup, preserve order, cap at 45 to stay under Deepgram's limit
    seen = set()
    out: list[str] = []
    for t in terms:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= 45:
            break
    return out


async def run_pipeline(
    transport: SmallWebRTCTransport,
    teaching_brain: TeachingBrainProcessor,
    response_recorder: ResponseRecorder,
    transcript_logger: TranscriptLogger,
    task_ref: list,
    lesson_id: str | None = None,
):
    print("[run_pipeline] Task started")
    try:
        print("[run_pipeline] Creating services...")
        keyterms = _build_deepgram_keyterms(lesson_id)
        print(f"[run_pipeline] Deepgram keyterms: {keyterms}")
        stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            settings=DeepgramSTTService.Settings(
                model="nova-3",
                language="en",
                smart_format=True,
                keyterm=keyterms if keyterms else None,
            ),
        )
        print("[run_pipeline] STT created")

        llm = AnthropicLLMService(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            settings=AnthropicLLMService.Settings(
                model="claude-sonnet-4-6",
                max_tokens=100,
                temperature=0.7,
            ),
        )
        print("[run_pipeline] LLM created")

        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            settings=ElevenLabsTTSService.Settings(
                voice=os.getenv("ELEVENLABS_VOICE_ID", "pFZP5JQG7iQjIQuC4Bku"),
                model="eleven_turbo_v2_5",
                language="ja",
                speed=0.85,
                stability=0.6,
                similarity_boost=0.8,
            ),
        )
        print("[run_pipeline] TTS created")

        pipeline = Pipeline([
            transport.input(),
            stt,
            teaching_brain,
            llm,
            response_recorder,
            tts,
            transport.output(),
            transcript_logger,
        ])

        task = PipelineTask(
            pipeline,
            params=PipelineParams(allow_interruptions=True, enable_metrics=True),
        )
        task_ref.append(task)
        print("[run_pipeline] Starting runner...")

        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)
        print("[run_pipeline] Runner finished")

    except Exception as e:
        import traceback
        print(f"[pipeline ERROR] {e}")
        traceback.print_exc()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.PIPECAT_HOST,
        port=settings.PIPECAT_PORT,
        log_level="info",
    )
