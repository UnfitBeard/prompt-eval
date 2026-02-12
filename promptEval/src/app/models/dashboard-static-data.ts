// models/dashboard-static-data.ts
//
// This file defines **static** course + module metadata that lives in
// the frontend. The dynamic dashboard merges this static structure with
// user-specific progress and scores returned by the backend.
//
// IMPORTANT: The `id` / `moduleId` fields here are intended to match
// real course and lesson IDs in MongoDB. They are currently populated
// with placeholder values to make the integration points explicit.
// Replace them with real IDs from your database when wiring things up
// end-to-end.

export interface StaticModuleDefinition {
  // This should be set to the backend lesson ID for the module.
  id: string;
  title: string;
  description?: string;
  // "Designed" XP for the module. The backend will report actual XP
  // earned; the dashboard can use this value for visual expectations.
  plannedXp: number;
}

export interface StaticCourseDefinition {
  // This should be the backend course ID.
  id: string;
  title: string;
  shortDescription?: string;
  estimatedHours?: number;
  modules: StaticModuleDefinition[];
}

// Example static definitions. These are intentionally small and
// focused on fields that are useful for the dashboard UI. You can
// expand this structure with anything else your product needs
// (e.g. target audience, tags, difficulty labels, etc.).

export const STATIC_COURSE_DEFINITIONS: StaticCourseDefinition[] = [
  {
    id: 'COURSE_ID_PROMPT_BASICS', // TODO: replace with real course ID
    title: 'Prompt Engineering Basics',
    shortDescription: 'Foundations of effective prompting and iteration.',
    estimatedHours: 6,
    modules: [
      {
        id: 'LESSON_ID_INTRO', // TODO: replace with real lesson ID
        title: 'Foundations: how LLMs respond to prompts',
        description: 'High-level mental model of LLMs and why prompts matter.',
        plannedXp: 50,
      },
      {
        id: 'LESSON_ID_STRUCTURE',
        title: 'Prompt anatomy and structure',
        description: 'Instructions, context, inputs, outputs, and examples.',
        plannedXp: 75,
      },
      {
        id: 'LESSON_ID_ITERATION',
        title: 'Iterative refinement loop',
        description: 'Try → observe → tweak patterns for improving prompts.',
        plannedXp: 75,
      },
    ],
  },
  {
    id: 'COURSE_ID_RAG',
    title: 'Retrieval-Augmented Generation (RAG)',
    shortDescription: 'Designing grounded, citation-rich RAG systems.',
    estimatedHours: 8,
    modules: [
      {
        id: 'LESSON_ID_RAG_ARCH',
        title: 'RAG architecture overview',
        description: 'Indexing, retrieval, and generation pipeline.',
        plannedXp: 80,
      },
      {
        id: 'LESSON_ID_RAG_PROMPTS',
        title: 'Grounding prompts with citations',
        description: 'Patterns for safe, evidence-based answers.',
        plannedXp: 100,
      },
    ],
  },
];
