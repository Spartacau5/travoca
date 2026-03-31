"use client";

import { UserProgress } from "@/types";

export function StreakCounter({ progress }: { progress: UserProgress | null }) {
  if (!progress) return null;

  const streak = progress.current_streak;

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 px-4 py-3 flex items-center gap-3">
      <div className="text-2xl">{streak > 0 ? "🔥" : "💤"}</div>
      <div>
        <div className="text-white font-semibold text-sm">
          {streak} day{streak !== 1 ? "s" : ""}
        </div>
        <div className="text-slate-400 text-xs">
          {streak === 0 ? "Start your streak!" : streak >= 7 ? "On fire!" : "Keep it up!"}
        </div>
      </div>
      {progress.longest_streak > 0 && (
        <div className="ml-auto text-right">
          <div className="text-xs text-slate-500">Best</div>
          <div className="text-xs text-amber-400 font-medium">{progress.longest_streak}d</div>
        </div>
      )}
    </div>
  );
}
