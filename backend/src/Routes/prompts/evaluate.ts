import express from 'express';
import {
  evaluate,
  evaluatePromptWithMyFlaskAI,
  recommendations,
} from '../../Controllers/Prompts/evaluate';

const router = express.Router();

router.post('/evaluate', evaluate);
router.post('/recommendations', recommendations);
router.post('/get-results', evaluatePromptWithMyFlaskAI);
export default router;
