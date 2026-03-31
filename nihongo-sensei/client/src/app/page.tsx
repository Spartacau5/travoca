"use client";

import { useState, useEffect } from "react";
import { VoiceAgent } from "@/components/VoiceAgent";
import { LessonPanel } from "@/components/LessonPanel";
import { TranscriptView } from "@/components/TranscriptView";
import { ProgressBar } from "@/components/ProgressBar";
import { StreakCounter } from "@/components/StreakCounter";
import { supabase, DEV_USER_ID } from "@/lib/supabase";
import { Lesson, UserProgress, TranscriptEntry } from "@/types";

export default function HomePage() {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);

  useEffect(() => {
    async function load() {
      const { data: user } = await supabase
        .from("users")
        .select("*")
        .eq("id", DEV_USER_ID)
        .single();
      if (user) setProgress(user);

      const { data: completed } = await supabase
        .from("lesson_progress")
        .select("lesson_id")
        .eq("user_id", DEV_USER_ID)
        .eq("status", "completed");

      const completedIds = (completed ?? []).map((r: { lesson_id: string }) => r.lesson_id);

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_PIPECAT_URL}/lessons`
        );
        if (res.ok) {
          const lessons: Lesson[] = await res.json();
          const current = lessons.find((l) => !completedIds.includes(l.id)) ?? lessons[0];
          setLesson(current);
        }
      } catch {
        // Server not yet running - lesson panel shows loading state
      }
    }
    load();
  }, []);

  const handleTranscript = (entry: TranscriptEntry) => {
    setTranscript((prev) => [...prev, entry]);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">日本語先生</h1>
          <p className="text-xs text-slate-400">Nihongo Sensei</p>
        </div>
        <div className="text-xs text-slate-500">Local Dev</div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-80 border-r border-slate-800 flex flex-col gap-4 p-4 overflow-y-auto">
          <ProgressBar progress={progress} />
          <StreakCounter progress={progress} />
          <LessonPanel lesson={lesson} />
        </aside>

        <main className="flex-1 flex flex-col">
          <div className="flex-1 p-6 overflow-hidden">
            <TranscriptView entries={transcript} />
          </div>

          <div className="border-t border-slate-800 p-8 flex items-center justify-center bg-slate-900">
            <VoiceAgent onTranscript={handleTranscript} />
          </div>
        </main>
      </div>
    </div>
  );
}
