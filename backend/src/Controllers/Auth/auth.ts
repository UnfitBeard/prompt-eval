import express from "express";
import dotenv from "dotenv";
import { Request, Response, NextFunction } from "express";
import { Collection, Db } from "mongodb";
import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import { generateToken } from "../../Utils/Helpers/generateToken";
dotenv.config();

export const registration =
  (db: Db) => async (req: Request, res: Response, next: NextFunction) => {
    const { username, email, password, organization } = req.body;

    if (!username || !password || !email) {
      return res.status(400).json({ message: "Missing credentials." });

      console.log("Error: Missing credentials");
    }

    try {
      const passwordHash = bcrypt.hashSync(password, 10);

      const users: Collection = db.collection("users");

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
    } catch (error) {
      console.error("Error: ", error);
      res.status(500).json({
        message: "Internal server error",
      });
    }
  };

export const login =
  (db: Db) => async (req: Request, res: Response, next: NextFunction) => {
    const { name, password } = req.body;

    if (!name || !password) {
      return res
        .status(400)
        .json({ message: "Email and password are required." });

      console.log("Error: Missing email or password in login request");
    }

    try {
      const users: Collection = db.collection("users");

      const user = await users.findOne({ name, password });

      if (!user) {
        return res.status(400).json({ message: "Invalid credentials." });
      }

      const passwordIsTrue = bcrypt.compareSync(password, user.password);

      if (!passwordIsTrue) {
        return res.status(401).json({
          message: "Wrong credentials",
        });
      }

      const tokens = await generateToken(res, user._id, user.email);

      return res
        .status(200)
        .json({ message: "Login successful", user, tokens: { tokens } });
    } catch (error) {
      console.error("Error during login:", error);
      return res.status(500).json({ message: "Internal server error." });
    }
  };
