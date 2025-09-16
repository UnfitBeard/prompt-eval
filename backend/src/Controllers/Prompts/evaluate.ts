import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import express from 'express';
import { Request, Response, NextFunction } from 'express';
import { Db, MongoClient } from 'mongodb';
import path from 'path';
import { readSync, writeFile, writeFileSync, mkdir } from 'fs';
import dotenv from 'dotenv';
dotenv.config();

const evaluationServiceUrl = 'http://localhost:5000/get-results';

const model = new ChatGoogleGenerativeAI({
  model: 'gemini-1.5-flash',
  temperature: 0.2,
  apiKey: process.env.GEMINI_API_KEY, // ensure it's set
});

export const evaluate = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { prompt } = (req.body ?? {}) as { prompt?: string };
    if (!prompt || typeof prompt !== 'string' || !prompt.trim()) {
      return res
        .status(400)
        .json({ error: "Missing or invalid 'prompt' in request body" });
    }

    const evaluation = await evaluatePrompt(prompt);
    return res.json(evaluation);
  } catch (err) {
    return next(err);
  }
};

const scorePrompt = (prompt: string) => `
Evaluate the following programming prompt. Score from 1 to 10 for:
- Clarity,
- Context
- Relevance
- Specificity
- Creativity

## Prompt:
"""
${prompt}
"""
Also generate three better versions of the prompt with the various metrics passing.
Three versions: minimalist, Enhanced and Alternative versions.
Also return suggestions for improvement.

Return the result in the following JSON format:
result = {"clarity": X, "relevance": X, "specificity": X, "creativity": X, "context": X}

suggestions = [
    {
      text: 'Consider adding more specific details about the character and their discovery',
    },
    {
      text: 'Add context about the setting and time period',
    },
  ];

  rewriteVersions = [
    {
      title: 'Enhanced Version',
      content:
        "Write a coming-of-age story about 16-year-old Sarah, who discovers an ancient magical portal in her family's overgrown backyard. The portal leads to a mystical forest where time flows differently, and she must navigate both worlds while keeping her discovery hidden from her skeptical parents.",
      improvements: [
        { text: 'Added specific character details' },
        { text: 'Included setting description' },
        { text: 'Introduced plot elements' },
      ],
    },
    {
      title: 'Alternative Version',
      content:
        'Create a story about a young inventor named Alex who discovers a mysterious portal in their backyard laboratory. The portal connects to a parallel universe where technology and magic coexist, forcing Alex to choose between their normal life and this extraordinary new world.',
      improvements: [
        { text: "Changed character's background" },
        { text: 'Added technological elements' },
        { text: 'Introduced conflict' },
      ],
    },
    {
      title: 'Minimalist Version',
      content:
        'Describe a scene where a character finds a glowing portal in their backyard. The portal emits a soft, warm light and seems to connect to an unknown dimension. The character approaches cautiously, their heart racing with anticipation.',
      improvements: [
        { text: 'Focused on atmosphere' },
        { text: 'Reduced character details' },
        { text: 'Emphasized sensory elements' },
      ],
    },
  ];
`;

async function evaluatePrompt(prompt: string) {
  const result = await model.invoke(scorePrompt(prompt));
  const content =
    typeof result.content === 'string'
      ? result.content
      : String((result as any)?.content ?? '');

  const match = content.match(/\{[\s\S]*?\}/);
  if (!match) return {};
  try {
    return JSON.parse(match[1]);
  } catch {
    return {};
  }
}

export const recommendations =
  (db: Db) => async (req: Request, res: Response, next: NextFunction) => {
    const prompt = req.body.prompt;
    const response = await fetch(evaluationServiceUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: prompt,
      }),
    });

    const result = await response.json();
    const resultJSON = result.values;
    const promptJSON = result.prompt;

    const recommendation = (
      prompt: string
    ) => `The following programming prompt ## Prompt:
"""${promptJSON}"""
 was evaluated based on the following metrics. Score from 1 to 10 for:
- Clarity,
- Context
- Relevance
- Specificity
- Creativity

and the result returned was """${resultJSON}"""

Based on the evaluation result,I want you to identify issues with the prompt and I want you to generate three variations of the same prompt for recommendation purposes.
Return result as JSON like:
{
      title: 'Enhanced Version',
      content:
        """${promptJSON}""",
      improvements: [
        { text: 'Added specific character details' },
        { text: 'Included setting description' },
        { text: 'Introduced plot elements' },
      ],
    },
`;
    const modelResult = await model.invoke(recommendation(promptJSON));
    const content =
      typeof modelResult.content === 'string'
        ? modelResult.content
        : String((modelResult as any)?.content ?? '');

    const match = content.match(/\{[\s\S]*?\}/);
    if (!match) {
      return {};
    }
    try {
      return JSON.parse(match[0]);
    } catch {
      return {};
    }
  };
