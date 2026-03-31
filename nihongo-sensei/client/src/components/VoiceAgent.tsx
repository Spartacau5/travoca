"use client";

import { useState, useCallback, useRef } from "react";
import { PipecatClient, RTVIEvent } from "@pipecat-ai/client-js";
import {
  PipecatClientProvider,
  usePipecatClient,
  useRTVIClientEvent,
} from "@pipecat-ai/client-react";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { PIPECAT_URL } from "@/lib/pipecat";
import { TranscriptEntry } from "@/types";

function VoiceControls({
  onTranscript,
}: {
  onTranscript: (entry: TranscriptEntry) => void;
}) {
  const client = usePipecatClient();
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [botSpeaking, setBotSpeaking] = useState(false);

  useRTVIClientEvent(RTVIEvent.Connected, () => setConnected(true));
  useRTVIClientEvent(RTVIEvent.Disconnected, () => {
    setConnected(false);
    setConnecting(false);
  });
  useRTVIClientEvent(RTVIEvent.BotStartedSpeaking, () => setBotSpeaking(true));
  useRTVIClientEvent(RTVIEvent.BotStoppedSpeaking, () => setBotSpeaking(false));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useRTVIClientEvent(RTVIEvent.UserTranscript, (data: any) => {
    if (data?.final && data?.text?.trim()) {
      onTranscript({ role: "user", text: data.text, timestamp: Date.now() });
    }
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useRTVIClientEvent(RTVIEvent.BotTranscript, (data: any) => {
    if (data?.text?.trim()) {
      onTranscript({ role: "assistant", text: data.text, timestamp: Date.now() });
    }
  });

  const handleConnect = useCallback(async () => {
    if (!client) return;
    setConnecting(true);
    try {
      // startBotAndConnect: POSTs to the endpoint, gets WebRTC params, connects
      await client.startBotAndConnect({ endpoint: PIPECAT_URL });
    } catch (e) {
      console.error("Connection failed:", e);
      setConnecting(false);
    }
  }, [client]);

  const handleDisconnect = useCallback(async () => {
    if (!client) return;
    await client.disconnect();
  }, [client]);

  return (
    <div className="flex flex-col items-center gap-6">
      <button
        onClick={connected ? handleDisconnect : handleConnect}
        disabled={connecting}
        className={`
          w-28 h-28 rounded-full text-white font-bold text-sm transition-all duration-200
          flex items-center justify-center shadow-lg
          ${connected
            ? "bg-red-500 hover:bg-red-600 ring-4 ring-red-400/40"
            : connecting
            ? "bg-slate-600 cursor-wait"
            : "bg-green-500 hover:bg-green-600"
          }
          ${botSpeaking ? "animate-pulse" : ""}
        `}
      >
        {connecting ? "Connecting..." : connected ? "End Lesson" : "Start Lesson"}
      </button>

      <div className="flex items-center gap-2 text-sm">
        <div
          className={`w-2 h-2 rounded-full ${
            connected ? "bg-green-400 animate-pulse" : "bg-slate-500"
          }`}
        />
        <span className="text-slate-400">
          {connected
            ? botSpeaking
              ? "Yuki is speaking..."
              : "Listening..."
            : "Ready to start"}
        </span>
      </div>
    </div>
  );
}

export function VoiceAgent({
  onTranscript,
}: {
  onTranscript: (entry: TranscriptEntry) => void;
}) {
  const clientRef = useRef<PipecatClient>(
    new PipecatClient({
      transport: new SmallWebRTCTransport(),
      enableMic: true,
      enableCam: false,
    })
  );

  return (
    <PipecatClientProvider client={clientRef.current}>
      <VoiceControls onTranscript={onTranscript} />
    </PipecatClientProvider>
  );
}
