"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const auth_1 = require("../../Controllers/Auth/auth");
const router = express_1.default.Router();
router.post("/login", auth_1.login);
router.post("/register", auth_1.registration);
exports.default = router;
