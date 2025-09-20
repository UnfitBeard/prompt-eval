// evalController.ts
import express, { Request, Response, NextFunction } from 'express';
import dotenv from 'dotenv';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { error } from 'console';

dotenv.config();

// ---- Config ----
const EVALUATION_SERVICE_URL =
  process.env.EVALUATION_SERVICE_URL ?? 'http://localhost:5000/get-results';

const GEMINI_MODEL = process.env.GEMINI_MODEL ?? 'gemini-1.5-flash';
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

if (!GEMINI_API_KEY) {
  // Fail fast so you don’t debug blind later
  console.warn('Warning: GEMINI_API_KEY is not set. Requests will fail.');
}

// ---- Model ----
const model = new ChatGoogleGenerativeAI({
  model: GEMINI_MODEL,
  temperature: 0.2,
  apiKey: GEMINI_API_KEY,
});

// ---- Helpers ----

/** Normalize LangChain message content to a plain string. */
function messageToString(content: unknown): string {
  if (typeof content === 'string') return content;
  // Some LangChain messages return an array of parts:
  // [{ type: 'text', text: '...' }, ...]
  try {
    if (Array.isArray(content)) {
      return content
        .map((p: any) => (typeof p?.text === 'string' ? p.text : ''))
        .join('\n');
    }
    return String(content ?? '');
  } catch {
    return '';
  }
}

/** Extract JSON from a fenced ```json code block or the first {...} block. */
function extractFirstJsonBlock(text: string): string | null {
  // Prefer fenced code blocks with json
  const fenced = text.match(/```json\s*([\s\S]*?)\s*```/i);
  if (fenced && fenced[1]) return fenced[1].trim();

  // Fallback: first JSON-looking object (greedy enough to include nested)
  const brace = text.match(/\{[\s\S]*\}/m);
  if (brace && brace[0]) return brace[0].trim();

  return null;
}

/** Safe JSON.parse with friendly failure. */
function tryParseJson<T = any>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

// ---- Prompt Templates ----

const scorePrompt = (userPrompt: string) => `
You are a strict evaluator for programming prompts.

Return ONLY JSON in a single fenced code block like:

\`\`\`json
{
  "clarity": 7.5,
  "context": 7.0,
  "relevance": 9.0,
  "specificity": 7.5,
  "creativity": 6.0,
  "suggestions": [
    { "text": "Add input/output examples." },
    { "text": "Specify language/runtime and constraints." }
  ],
  "rewriteVersions": [
    {
      "title": "Enhanced Version",
      "content": "....",
      "improvements": [{ "text": "..." }]
    },
    {
      "title": "Alternative Version",
      "content": "....",
      "improvements": [{ "text": "..." }]
    },
    {
      "title": "Minimalist Version",
      "content": "....",
      "improvements": [{ "text": "..." }]
    }
  ]
}
\`\`\`

Scoring scale: 1–10 (decimals allowed).

PROMPT TO EVALUATE:
"""${userPrompt}"""
`;

const recommendPrompt = (origPrompt: string, resultJson: any) => `
You are an assistant improving a programming prompt.

Given the original prompt and its evaluation results, produce ONLY JSON in a single fenced code block:

\`\`\`json
{
  "rewriteVersions": [
    {
      "title": "Enhanced Version",
      "content": "string",
      "improvements": [{ "text": "string" }]
    },
    {
      "title": "Alternative Version",
      "content": "string",
      "improvements": [{ "text": "string" }]
    },
    {
      "title": "Minimalist Version",
      "content": "string",
      "improvements": [{ "text": "string" }]
    }
  ],
  "notes": [
    { "text": "Brief rationale about how the rewrites improve clarity/context/specificity." }
  ]
}
\`\`\`

ORIGINAL PROMPT:
"""${origPrompt}"""

EVALUATION RESULT (JSON):
${JSON.stringify(resultJson, null, 2)}
`;

// ---- Core functions ----

export async function evaluatePromptWithGemini(userPrompt: string) {
  const msg = await model.invoke(scorePrompt(userPrompt));
  const text = messageToString((msg as any)?.content);
  const jsonRaw = extractFirstJsonBlock(text);
  const parsed = tryParseJson(jsonRaw);

  // If parsing failed, return a minimal object to avoid 500s
  if (!parsed) {
    return {
      clarity: null,
      context: null,
      relevance: null,
      specificity: null,
      creativity: null,
      suggestions: [],
      rewriteVersions: [],
      _raw: text,
      _error: 'Failed to parse JSON from model output.',
    };
  }
  return parsed;
}

// ---- Express handlers ----

/**
 * POST /api/evaluate
 * body: { prompt: string }
 */
export async function evaluate(
  req: Request,
  res: Response,
  next: NextFunction
) {
  try {
    const prompt = String(req.body?.prompt ?? '').trim();
    if (!prompt) {
      return res
        .status(400)
        .json({ error: "Missing or invalid 'prompt' in request body" });
    }
    const evaluation = await evaluatePromptWithGemini(prompt);
    return res.status(200).json(evaluation);
  } catch (err) {
    return next(err);
  }
}

/**
 * POST /api/recommendations
 * body: { prompt: string }
 *
 * Calls your external evaluation service first (optional),
 * then asks Gemini to produce 3 rewrite versions as JSON.
 */
export function recommendations() {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const prompt = String(req.body?.prompt ?? '').trim();
      if (!prompt) {
        return res
          .status(400)
          .json({ error: "Missing or invalid 'prompt' in request body" });
      }

      // Step 1: call external service (optional in your flow)
      const resp = await fetch(EVALUATION_SERVICE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      if (!resp.ok) {
        const msg = await resp.text().catch(() => '');
        return res
          .status(502)
          .json({ error: 'Upstream evaluation failed', detail: msg });
      }

      const result = (await resp.json().catch(() => ({}))) as any;
      const resultJSON = result?.values ?? result?.result ?? result ?? {};
      const promptJSON = result?.prompt ?? prompt;

      // Step 2: ask Gemini for rewrites
      const llm = await model.invoke(recommendPrompt(promptJSON, resultJSON));
      const text = messageToString((llm as any)?.content);
      const jsonRaw = extractFirstJsonBlock(text);
      const parsed = tryParseJson(jsonRaw);

      if (!parsed) {
        return res.status(200).json({
          rewriteVersions: [],
          notes: [],
          _raw: text,
          _error: 'Failed to parse JSON from model output.',
        });
      }

      return res.status(200).json(parsed);
    } catch (err) {
      return next(err);
    }
  };
}

export const evaluatePromptWithMyFlaskAI = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const { prompt } = req.body;

  if (!prompt) {
    return res.status(204).json({ message: 'Missing prompt' });
  }

  try {
    const result = await fetch('http://localhost:5000/evaluate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });

    if (!result.ok) {
      const text = await result.text().catch(() => '');
      return res
        .status(502)
        .json({ error: 'Flask evaluate failed', detail: text });
    }

    const response = await result.json();
    console.log(result);
    return res.status(200).json(response);
  } catch (error) {
    console.error(error);
    res.status(500).json('Internal Server Error Buoy');
  }
};
