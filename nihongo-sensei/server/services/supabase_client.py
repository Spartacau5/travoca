import os
import json
from datetime import datetime
from supabase import create_client, Client


class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        self.client: Client = create_client(url, key)

    async def get_user(self, user_id: str) -> dict:
        result = self.client.table("users").select("*").eq("id", user_id).single().execute()
        return result.data

    async def get_user_progress(self, user_id: str) -> dict:
        user = await self.get_user(user_id)
        progress = self.client.table("lesson_progress").select("*").eq("user_id", user_id).execute()
        return {**user, "lessons": progress.data}

    async def get_current_lesson_id(self, user_id: str) -> str:
        completed = (
            self.client.table("lesson_progress")
            .select("lesson_id")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
        )
        completed_ids = [r["lesson_id"] for r in completed.data]
        from curriculum.lessons import get_next_incomplete_lesson
        lesson = get_next_incomplete_lesson(completed_ids)
        return lesson["id"]

    async def create_session(self, user_id: str, lesson_id: str) -> str:
        result = (
            self.client.table("session_logs")
            .insert({"user_id": user_id, "lesson_id": lesson_id})
            .execute()
        )
        return result.data[0]["id"]

    async def finalize_session(
        self,
        session_id: str,
        turn_count: int,
        avg_pronunciation: float | None,
        transcript: list,
    ):
        self.client.table("session_logs").update({
            "ended_at": datetime.utcnow().isoformat(),
            "turn_count": turn_count,
            "avg_pronunciation_score": avg_pronunciation,
            "transcript": transcript,
        }).eq("id", session_id).execute()

    async def update_user(self, user_id: str, data: dict):
        self.client.table("users").update(data).eq("id", user_id).execute()

    async def award_xp(self, user_id: str, xp: int):
        user = await self.get_user(user_id)
        new_xp = user["total_xp"] + xp
        from processors.gamification import GamificationEngine
        engine = GamificationEngine()
        new_level = engine.get_level(new_xp)
        self.client.table("users").update({
            "total_xp": new_xp,
            "current_level": new_level["level"],
        }).eq("id", user_id).execute()

    async def complete_lesson(self, user_id: str, lesson_id: str, score: int, xp: int):
        self.client.table("lesson_progress").upsert({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "status": "completed",
            "score": score,
            "xp_earned": xp,
            "attempts": 1,
        }).execute()
