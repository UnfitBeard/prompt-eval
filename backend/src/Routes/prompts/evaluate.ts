import express from "express";
import { evaluate, recommendations } from "../../Controllers/Prompts/evaluate";

const router = express.Router();

router.post("/evaluate", evaluate);
router.post("/recommendations", recommendations);
export default router;
