"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.recommendations = exports.evaluate = void 0;
const google_genai_1 = require("@langchain/google-genai");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const evaluationServiceUrl = "http://localhost:5000/get-results";
const model = new google_genai_1.ChatGoogleGenerativeAI({
    model: "gemini-1.5-flash",
    temperature: 0.2,
    apiKey: process.env.GEMINI_API_KEY, // ensure it's set
});
const evaluate = async (req, res, next) => {
    try {
        const { prompt } = (req.body ?? {});
        if (!prompt || typeof prompt !== "string" || !prompt.trim()) {
            return res
                .status(400)
                .json({ error: "Missing or invalid 'prompt' in request body" });
        }
        const evaluation = await evaluatePrompt(prompt);
        return res.json(evaluation);
    }
    catch (err) {
        return next(err);
    }
};
exports.evaluate = evaluate;
const scorePrompt = (prompt) => `
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

Return result as JSON like:
{"clarity": X, "relevance": X, "specificity": X, "creativity": X, "context": X}
`;
async function evaluatePrompt(prompt) {
    const result = await model.invoke(scorePrompt(prompt));
    const content = typeof result.content === "string"
        ? result.content
        : String(result?.content ?? "");
    const match = content.match(/\{[\s\S]*?\}/);
    if (!match)
        return {};
    try {
        return JSON.parse(match[0]);
    }
    catch {
        return {};
    }
}
const recommendations = (db) => async (req, res, next) => {
    const prompt = req.body.prompt;
    const response = await fetch(evaluationServiceUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: prompt,
        }),
    });
    const result = await response.json();
    const resultJSON = result.values;
    const promptJSON = result.prompt;
    const recommendation = (prompt) => `The following programming prompt ## Prompt:
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
    const content = typeof modelResult.content === "string"
        ? modelResult.content
        : String(modelResult?.content ?? "");
    const match = content.match(/\{[\s\S]*?\}/);
    if (!match) {
        return {};
    }
    try {
        return JSON.parse(match[0]);
    }
    catch {
        return {};
    }
};
exports.recommendations = recommendations;
