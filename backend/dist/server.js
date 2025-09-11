"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config(); // load env vars FIRST
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const mongodb_1 = require("mongodb");
const auth_1 = __importDefault(require("./src/Routes/Auth/auth"));
const evaluate_1 = __importDefault(require("./src/Routes/prompts/evaluate"));
const app = (0, express_1.default)();
const PORT = Number(process.env.PORT) || 3000;
app.use((0, cors_1.default)({
    origin: "*",
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
}));
app.use(express_1.default.json({ limit: "1mb" }));
app.use(express_1.default.urlencoded({ extended: true, limit: "1mb" }));
const uri = process.env.MONGO_DB_URI;
// Create a MongoClient with a MongoClientOptions object to set the Stable API version
const client = new mongodb_1.MongoClient(uri, {
    serverApi: {
        version: mongodb_1.ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    },
});
async function run() {
    try {
        // Connect the client to the server	(optional starting in v4.7)
        await client.connect();
        // Send a ping to confirm a successful connection
        await client.db("admin").command({ ping: 1 });
        console.log("Pinged your deployment. You successfully connected to MongoDB!");
        app.use("/api/v1/auth", auth_1.default);
        app.use("/api/v1/prompts", evaluate_1.default);
        app.get("/", (_req, res) => {
            res.send("Welcome to the backend server!");
        });
        // Basic error handler (optional but useful)
        app.use((err, _req, res, _next) => {
            console.error(err);
            res.status(500).json({ error: "Internal Server Error" });
        });
    }
    finally {
        // Ensures that the client will close when you finish/error
        await client.close();
    }
}
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
run().catch((e) => {
    console.error("Failed to start:", e);
    process.exit(1);
});
