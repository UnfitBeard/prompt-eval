import dotenv from 'dotenv';
dotenv.config(); // load env vars FIRST

import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { MongoClient, ServerApiVersion } from 'mongodb';
import authRoutes from './src/Routes/Auth/auth';
import promptRoutes from './src/Routes/prompts/evaluate';
import mongoose, { mongo } from 'mongoose';

const app = express();
const PORT = Number(process.env.PORT) || 10000;

const allowedOrigins = [
  'http://localhost:4200',
  'https://prompt-eval-xfmd.vercel.app/',
];

app.use(
  cors({
    origin: allowedOrigins,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));
app.get('/health', (_req, res) => res.status(200).send('ok'));
app.get('/', (_req, res) => res.send('Welcome'));

const uri: string = process.env.MONGO_DB_URI!;
// Create a MongoClient with a MongoClientOptions object to set the Stable API version
async function run() {
  try {
    // Connect the client to the server	(optional starting in v4.7)
    await mongoose.connect(uri);
    // Send a ping to confirm a successful connection
    await mongoose.connection.db?.command({ ping: 1 });
    console.log(
      'Pinged your deployment. You successfully connected to MongoDB!'
    );

    app.use('/api/v1/auth', authRoutes);
    app.use('/api/v1/prompts', promptRoutes);

    // Basic error handler (optional but useful)
    app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
      console.error(err);
      res.status(500).json({ error: 'Internal Server Error' });
    });
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
  }
}

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on port ${PORT}`);
});

run().catch((e) => {
  console.error('Failed to start:', e);
  process.exit(1);
});
