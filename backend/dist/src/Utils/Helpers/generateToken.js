"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateToken = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config;
const generateToken = async (res, user_id, email) => {
    const jwtSecret = process.env["JWT_SECRET"];
    const refreshSecret = process.env["REFRESH_TOKEN_SECRET"];
    if (!jwtSecret || !refreshSecret) {
        throw new Error("JWT_SECRET or REFRESH_TOKEN_SECRET is not defined in environment variables");
    }
    try {
        const accessToken = jsonwebtoken_1.default.sign({
            user_id,
            email,
        }, jwtSecret, {
            expiresIn: "15m",
        });
        const refreshToken = jsonwebtoken_1.default.sign({
            user_id,
        }, refreshSecret, { expiresIn: "30d" });
        res.cookie("access_token", accessToken, {
            httpOnly: true,
            sameSite: "lax",
            maxAge: 15 * 60 * 100,
        });
        res.cookie("refresh_token", refreshToken, {
            httpOnly: true,
            sameSite: "lax",
            maxAge: 15 * 60 * 100,
        });
        return { accessToken, refreshToken };
    }
    catch (error) {
        console.error("Error generating JWT:", error);
        throw new Error("Error generating authentication tokens");
    }
};
exports.generateToken = generateToken;
