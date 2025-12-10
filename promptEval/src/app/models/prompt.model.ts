// models/prompt.model.ts
export interface PromptEvaluationRequest {
  prompt: string;
  k?: number;
  improve_if_low?: boolean;
}

export interface PromptScores {
  base_scores: {
    clarity: number;
    context: number;
    relevance: number;
    specificity: number;
    creativity: number;
  };
  final_scores: {
    clarity: number;
    context: number;
    relevance: number;
    specificity: number;
    creativity: number;
  };
}

export interface SimilarPrompt {
  content: string;
  metadata: {
    source_url?: string;
    page_title?: string;
    prompt_preview?: string;
    parent_row?: number;
  };
  similarity?: number;
  source: string;
}

export interface ImprovedVersion {
  content: string;
  explanation: string;
  changes: string[];
}

export interface PromptEvaluationResult {
  prompt: string;
  scores: PromptScores;
  overall_score: number;
  needs_improvement: boolean;
  suggestions: string[];
  similar_prompts: SimilarPrompt[];
  improved_version?: ImprovedVersion;
  trace_id: string;
  processing_time_ms: number;
}

export interface EvaluationHistory {
  id: string;
  prompt: string;
  timestamp: string;
  base_scores: any;
  final_scores: any;
  overall_score: number;
  suggestions: string[];
  improved_prompt: string;
  improved_scores: any;
  trace_id: string;
}
