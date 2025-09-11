"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.login = exports.registration = void 0;
const dotenv_1 = __importDefault(require("dotenv"));
const bcryptjs_1 = __importDefault(require("bcryptjs"));
const generateToken_1 = require("../../Utils/Helpers/generateToken");
dotenv_1.default.config();
const registration = (db) => async (req, res, next) => {
    const { username, email, password, organization } = req.body;
    if (!username || !password || !email) {
        return res.status(400).json({ message: "Missing credentials." });
        console.log("Error: Missing credentials");
    }
    try {
        const passwordHash = bcryptjs_1.default.hashSync(password, 10);
        const users = db.collection("users");
        if (!users) {
            await db.createCollection(users);
            console.log("Created new users table as it was non existent");
        }
        const newUser = await users.insertOne({
            username: username,
            email: email,
            password: password,
            organization: organization,
        });
        if (newUser.insertedId) {
            return res.status(401).json({
                message: "Could not add new user try again later",
            });
        }
        res.status(201).json({
            message: "User created successfully",
            user: {
                id: newUser.insertedId,
                username: username,
                email: email,
                organization: organization,
            },
        });
    }
    catch (error) {
        console.error("Error: ", error);
        res.status(500).json({
            message: "Internal server error",
        });
    }
};
exports.registration = registration;
const login = (db) => async (req, res, next) => {
    const { name, password } = req.body;
    if (!name || !password) {
        return res
            .status(400)
            .json({ message: "Email and password are required." });
        console.log("Error: Missing email or password in login request");
    }
    try {
        const users = db.collection("users");
        const user = await users.findOne({ name, password });
        if (!user) {
            return res.status(400).json({ message: "Invalid credentials." });
        }
        const passwordIsTrue = bcryptjs_1.default.compareSync(password, user.password);
        if (!passwordIsTrue) {
            return res.status(401).json({
                message: "Wrong credentials",
            });
        }
        const tokens = await (0, generateToken_1.generateToken)(res, user._id, user.email);
        return res
            .status(200)
            .json({ message: "Login successful", user, tokens: { tokens } });
    }
    catch (error) {
        console.error("Error during login:", error);
        return res.status(500).json({ message: "Internal server error." });
    }
};
exports.login = login;
