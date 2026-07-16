// Types for pre-computed JSON data

export interface ChartDataItem {
  name: string;
  count: number;
}

export interface Section1Data {
  total: number;
  languages: ChartDataItem[];
  databases: ChartDataItem[];
  clouds: ChartDataItem[];
  frontend_frameworks: ChartDataItem[];
}

export interface MetricsData {
  generated_at_utc: string;
  total_messages: number;
  entry_level_messages: number;
  entry_level_share_percent: number;
  messages_with_ai_dev_tools: number;
  ai_dev_tools_share_percent: number;
  date_span: string;
  years: Record<string, { total: number; entry_level: number }>;
}

export interface AiToolsTimeline {
  months: string[];
  tools: Record<string, number[]>;
  total_per_month: number[];
  offers_with_ai_per_month?: number[];
}

export interface MonthlyVolume {
  month: string;
  count: number;
}

export interface SeniorityShiftYear {
  year: string;
  total: number;
  practice: number;
  junior: number;
  semi_senior: number;
  senior: number;
  unknown: number;
}

export interface TechTrends {
  years: string[];
  technologies: Record<string, number[]>;
}

export type YearFilter = 'all' | '2023' | '2024' | '2025' | '2026';
export type SeniorityFilter = 'all' | 'practice' | 'junior' | 'semi_senior' | 'senior';
