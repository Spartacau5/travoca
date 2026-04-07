"use client";

import { useState } from "react";
import { Lesson } from "@/types";

export function LessonPanel({ lesson }: { lesson: Lesson | null }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!lesson) {
    return (
      <div className="text-slate-500 text-sm p-4">Loading lesson...</div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-750 transition-colors"
      >
        <div>
          <span className="text-green-400 font-semibold text-sm">{lesson.title_ja}</span>
          <span className="text-slate-400 text-sm ml-2">/ {lesson.title}</span>
          <span className="ml-2 text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">
            {lesson.level}
          </span>
        </div>
        <span className="text-slate-500 text-xs">{collapsed ? "Show" : "Hide"}</span>
      </button>

      {!collapsed && (
        <div className="px-4 pb-4 space-y-4">
          <p className="text-slate-400 text-xs">{lesson.description}</p>

          {lesson.vocabulary.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Vocabulary
              </h3>
              <div className="space-y-2">
                {lesson.vocabulary.map((v) => (
                  <div key={v.word} className="flex items-start gap-3 text-sm">
                    <div className="min-w-0">
                      <span className="text-white font-bold text-base">{v.word}</span>
                      {v.reading !== v.word && (
                        <span className="text-slate-400 text-xs ml-1">({v.reading})</span>
                      )}
                      <span className="block text-green-400 text-xs mt-0.5">{v.meaning}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {lesson.grammar.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Grammar
              </h3>
              <div className="space-y-2">
                {lesson.grammar.map((g) => (
                  <div key={g.pattern} className="text-sm">
                    <span className="text-green-400 font-mono">{g.pattern}</span>
                    <span className="text-slate-400 text-xs ml-2">— {g.explanation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Today's Scenario
            </h3>
            <p className="text-slate-400 text-xs">
              {lesson.conversation_scenario.setting}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
