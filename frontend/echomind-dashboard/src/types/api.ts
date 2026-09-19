export interface SystemStatus {
  application: string;
  web: string;
  database: "connected" | "error" | string;
  listening: "active" | "paused" | string;
}

export interface ApiStatusResponse {
  available: boolean;
  status?: SystemStatus;
  error?: string;
}

export interface Memory {
  id: number;
  category: string;
  title: string;
  content: string;
  date: string;
  time: string;
  notification: boolean;
  status: string;
  seen_count: number;
  supersedes_id: number | null;
}

export interface ApiMemoriesResponse {
  available: boolean;
  memories?: Memory[];
  error?: string;
}

export type MemoryCategory =
  | "All"
  | "Reminder"
  | "Task"
  | "Shopping"
  | "Note"
  | "Preference"
  | "Event";

export interface Reminder {
  id: number;
  memory_id: number;
  reminder_time: string;
  status: string;
  created_at: string;
  triggered_at: string | null;
  title: string;
  content: string;
}
