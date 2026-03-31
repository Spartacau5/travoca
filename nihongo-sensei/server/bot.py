"""
Nihongo Sensei - Pipecat voice pipeline
Run with: python bot.py

Pipeline: Audio In -> Deepgram STT -> Teaching Brain -> Claude LLM -> ElevenLabs TTS -> Audio Out

Uses FastAPI + SmallWebRTCRequestHandler (pipecat 0.0.108 API).
The client connects by POSTing a WebRTC offer to /api/offer.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import uvicorn
from fastapi import BackgroundTasks, FastAPI
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
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from processors.teaching_brain import TeachingBrainProcessor
from processors.lesson_manager import LessonManager
from processors.transcript_logger import TranscriptLogger
from curriculum.lessons import get_all_lessons
from config import settings

load_dotenv()

# --- HTTP Server ---

small_webrtc_handler = SmallWebRTCRequestHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()
    yield
    await small_webrtc_handler.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/lessons")
async def list_lessons():
    """Return the full lesson list so the client can display the current lesson."""
    return JSONResponse(content=get_all_lessons())


@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks):
    """Handle WebRTC offer from the browser client."""

    async def webrtc_connection_callback(connection: SmallWebRTCConnection):
        background_tasks.add_task(run_bot, connection)

    answer = await small_webrtc_handler.handle_web_request(
        request=request,
        webrtc_connection_callback=webrtc_connection_callback,
    )
    return answer


@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    """Handle ICE candidate trickling."""
    await small_webrtc_handler.handle_patch_request(request)
    return {"status": "ok"}


# --- Bot pipeline (runs once per WebRTC connection) ---

async def run_bot(webrtc_connection: SmallWebRTCConnection):
    from pipecat.transports.base_transport import TransportParams

    transport_params = TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    )

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=transport_params,
    )

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        params=DeepgramSTTService.InputParams(
            model="nova-3",
            language="multi",
            smart_format=True,
        ),
    )

    llm = AnthropicLLMService(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-sonnet-4-6",
        params=AnthropicLLMService.InputParams(
            max_tokens=300,
            temperature=0.7,
        ),
    )

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        params=ElevenLabsTTSService.InputParams(
            model="eleven_multilingual_v2",
            language="ja",
            optimize_streaming_latency=3,
        ),
    )

    lesson_manager = LessonManager()
    teaching_brain = TeachingBrainProcessor(lesson_manager=lesson_manager)
    transcript_logger = TranscriptLogger()

    pipeline = Pipeline([
        transport.input(),
        stt,
        teaching_brain,
        llm,
        tts,
        transport.output(),
        transcript_logger,
    ])

    task = PipelineTask(
        pipeline,
        PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        print("Learner connected! Starting lesson...")
        await teaching_brain.start_lesson()

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        print("Learner disconnected. Saving progress...")
        await teaching_brain.end_session()
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.PIPECAT_HOST,
        port=settings.PIPECAT_PORT,
        log_level="info",
    )
