"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const evaluate_1 = require("../../Controllers/Prompts/evaluate");
const router = express_1.default.Router();
router.post("/evaluate", evaluate_1.evaluate);
router.post("/recommendations", evaluate_1.recommendations);
exports.default = router;
