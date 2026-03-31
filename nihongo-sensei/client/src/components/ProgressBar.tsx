"use client";

import { UserProgress } from "@/types";

const LEVELS = [
  { level: 1, xp: 0, title: "Beginner" },
  { level: 2, xp: 200, title: "Novice" },
  { level: 3, xp: 500, title: "Student" },
  { level: 4, xp: 1000, title: "Learner" },
  { level: 5, xp: 2000, title: "Speaker" },
  { level: 6, xp: 4000, title: "Conversationalist" },
  { level: 7, xp: 7000, title: "Advanced" },
  { level: 8, xp: 11000, title: "Fluent" },
  { level: 9, xp: 16000, title: "Master" },
  { level: 10, xp: 25000, title: "Sensei" },
];

function getLevelInfo(totalXp: number) {
  let current = LEVELS[0];
  let next = LEVELS[1];
  for (let i = 0; i < LEVELS.length; i++) {
    if (totalXp >= LEVELS[i].xp) {
      current = LEVELS[i];
      next = LEVELS[i + 1] ?? LEVELS[i];
    }
  }
  const xpIntoLevel = totalXp - current.xp;
  const xpNeeded = next.xp - current.xp;
  const pct = current.level === 10 ? 100 : Math.min(100, Math.round((xpIntoLevel / xpNeeded) * 100));
  return { current, next, pct, xpIntoLevel, xpNeeded };
}

export function ProgressBar({ progress }: { progress: UserProgress | null }) {
  if (!progress) return null;

  const { current, next, pct, xpIntoLevel, xpNeeded } = getLevelInfo(progress.total_xp);

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold text-sm">
            Lv.{current.level} {current.title}
          </span>
        </div>
        <span className="text-slate-400 text-xs">{progress.total_xp.toLocaleString()} XP</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div
          className="bg-green-500 h-2 rounded-full transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
      {current.level < 10 && (
        <div className="text-right text-xs text-slate-500 mt-1">
          {xpIntoLevel} / {xpNeeded} XP to {next.title}
        </div>
      )}
    </div>
  );
}
