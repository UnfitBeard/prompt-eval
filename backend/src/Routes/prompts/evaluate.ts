import express from 'express';
import {
  evaluate,
  evaluatePromptWithMyFlaskAI,
  recommendations,
} from '../../Controllers/Prompts/evaluate';
import { addTemplate, getTemplates } from '../../Controllers/Prompts/templates';

const router = express.Router();

router.post('/evaluate', evaluate);
router.post('/get-results', evaluatePromptWithMyFlaskAI);
router.post('/recommendations', recommendations);
router.post('/admin/templates', addTemplate);
router.post('/get-templates', getTemplates);
export default router;
