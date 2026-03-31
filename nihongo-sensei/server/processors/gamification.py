from datetime import date

XP_REWARDS = {
    "lesson_complete": 100,
    "perfect_score": 50,
    "new_vocab_mastered": 20,
    "streak_bonus_per_day": 10,
    "pronunciation_perfect": 30,
    "first_try_correct": 15,
}

LEVELS = [
    {"level": 1, "xp": 0, "title": "Beginner", "title_ja": "初心者"},
    {"level": 2, "xp": 200, "title": "Novice", "title_ja": "入門者"},
    {"level": 3, "xp": 500, "title": "Student", "title_ja": "学生"},
    {"level": 4, "xp": 1000, "title": "Learner", "title_ja": "学習者"},
    {"level": 5, "xp": 2000, "title": "Speaker", "title_ja": "話者"},
    {"level": 6, "xp": 4000, "title": "Conversationalist", "title_ja": "会話上手"},
    {"level": 7, "xp": 7000, "title": "Advanced", "title_ja": "上級者"},
    {"level": 8, "xp": 11000, "title": "Fluent", "title_ja": "流暢"},
    {"level": 9, "xp": 16000, "title": "Master", "title_ja": "達人"},
    {"level": 10, "xp": 25000, "title": "Sensei", "title_ja": "先生"},
]


class GamificationEngine:

    def calculate_xp(
        self,
        score: int,
        vocab_mastered: list,
        pronunciation_avg: float | None,
        streak: int,
    ) -> int:
        xp = XP_REWARDS["lesson_complete"]
        if score >= 90:
            xp += XP_REWARDS["perfect_score"]
        xp += len(vocab_mastered) * XP_REWARDS["new_vocab_mastered"]
        if pronunciation_avg and pronunciation_avg >= 90:
            xp += XP_REWARDS["pronunciation_perfect"]
        streak_bonus = min(streak * XP_REWARDS["streak_bonus_per_day"], 50)
        xp += streak_bonus
        return xp

    def get_level(self, total_xp: int) -> dict:
        current = LEVELS[0]
        for level in LEVELS:
            if total_xp >= level["xp"]:
                current = level
        return current

    def check_level_up(self, old_xp: int, new_xp: int) -> dict | None:
        old_level = self.get_level(old_xp)
        new_level = self.get_level(new_xp)
        if new_level["level"] > old_level["level"]:
            return new_level
        return None

    async def update_streak(self, user_id: str, db) -> dict:
        user = await db.get_user(user_id)
        today = date.today()
        last_active = user.get("last_active_date")

        if last_active:
            last_active = date.fromisoformat(str(last_active))
            diff = (today - last_active).days
            if diff == 0:
                return {"streak": user["current_streak"], "changed": False}
            elif diff == 1:
                new_streak = user["current_streak"] + 1
            else:
                new_streak = 1
        else:
            new_streak = 1

        longest = max(new_streak, user.get("longest_streak", 0))
        await db.update_user(user_id, {
            "current_streak": new_streak,
            "longest_streak": longest,
            "last_active_date": today.isoformat(),
        })
        return {
            "streak": new_streak,
            "changed": True,
            "is_new_record": new_streak > user.get("longest_streak", 0),
        }
