export interface VocabEntry {
  word: string;
  reading: string;
  meaning: string;
  example: string;
  example_translation: string;
}

export interface GrammarPoint {
  pattern: string;
  explanation: string;
  examples: { ja: string; en: string }[];
}

export interface ConversationScenario {
  setting: string;
  sensei_role: string;
  learner_goal: string;
  starter_prompt: string;
  key_phrases: string[];
}

export interface Lesson {
  id: string;
  unit: number;
  order: number;
  title: string;
  title_ja: string;
  level: string;
  type: string;
  description: string;
  objectives: string[];
  vocabulary: VocabEntry[];
  grammar: GrammarPoint[];
  conversation_scenario: ConversationScenario;
  xp_reward: number;
  passing_score: number;
}

export interface UserProgress {
  id: string;
  display_name: string;
  current_level: number;
  total_xp: number;
  current_streak: number;
  longest_streak: number;
  last_active_date: string | null;
}

export interface TranscriptEntry {
  role: "user" | "assistant";
  text: string;
  timestamp: number;
}
