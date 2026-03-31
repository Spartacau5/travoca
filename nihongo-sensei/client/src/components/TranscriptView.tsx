"use client";

import { useEffect, useRef } from "react";
import { TranscriptEntry } from "@/types";

export function TranscriptView({ entries }: { entries: TranscriptEntry[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        Conversation will appear here when you start a lesson.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 overflow-y-auto h-full pr-1">
      {entries.map((entry, i) => (
        <div
          key={i}
          className={`flex ${entry.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm leading-relaxed
              ${entry.role === "user"
                ? "bg-green-600 text-white rounded-br-sm"
                : "bg-slate-700 text-slate-100 rounded-bl-sm"
              }
            `}
          >
            <div className="text-xs opacity-60 mb-1 font-medium">
              {entry.role === "user" ? "You" : "Yuki-sensei"}
            </div>
            {entry.text}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
