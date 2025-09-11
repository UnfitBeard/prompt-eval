import express from "express";
import { login, registration } from "../../Controllers/Auth/auth";

const router = express.Router();

router.post("/login", login);
router.post("/register", registration);
export default router;
