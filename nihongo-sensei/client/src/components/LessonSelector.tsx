"use client";

import { Lesson } from "@/types";

export function LessonSelector({
  lessons,
  currentLesson,
  onSelect,
}: {
  lessons: Lesson[];
  currentLesson: Lesson | null;
  onSelect: (lesson: Lesson) => void;
}) {
  if (lessons.length === 0) return null;

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-3">
      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
        Lessons
      </h3>
      <div className="space-y-1">
        {lessons.map((lesson, i) => {
          const isActive = currentLesson?.id === lesson.id;
          return (
            <button
              key={lesson.id}
              onClick={() => onSelect(lesson)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-green-600/20 border border-green-500/40 text-white"
                  : "hover:bg-slate-700 text-slate-400 hover:text-white"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs text-slate-500 w-4 shrink-0">{i + 1}</span>
                  <span className={`truncate ${isActive ? "font-semibold" : ""}`}>
                    {lesson.title}
                  </span>
                </div>
                <span className="text-xs text-slate-500 shrink-0 ml-2">{lesson.level}</span>
              </div>
              <div className="text-xs text-slate-500 ml-6 truncate">{lesson.title_ja}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
