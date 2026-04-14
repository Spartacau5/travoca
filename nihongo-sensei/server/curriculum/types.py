from typing import TypedDict, Optional


class VocabEntry(TypedDict):
    word: str
    reading: str
    romaji: str
    meaning: str
    example: str
    example_translation: str


class GrammarPoint(TypedDict):
    pattern: str
    explanation: str
    examples: list[dict]


class ConversationScenario(TypedDict):
    setting: str
    sensei_role: str
    learner_goal: str
    starter_prompt: str
    key_phrases: list[str]


class Lesson(TypedDict):
    id: str
    unit: int
    order: int
    title: str
    title_ja: str
    level: str
    type: str
    description: str
    objectives: list[str]
    vocabulary: list[VocabEntry]
    grammar: list[GrammarPoint]
    conversation_scenario: ConversationScenario
    xp_reward: int
    passing_score: int
