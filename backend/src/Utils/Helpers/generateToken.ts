import jwt from "jsonwebtoken";
import { Response } from "express";
import dotenv from "dotenv";
import { ObjectId } from "mongodb";
dotenv.config;

export const generateToken = async (
  res: Response,
  user_id: ObjectId,
  email: string
) => {
  const jwtSecret = process.env["JWT_SECRET"];
  const refreshSecret = process.env["REFRESH_TOKEN_SECRET"];

  if (!jwtSecret || !refreshSecret) {
    throw new Error(
      "JWT_SECRET or REFRESH_TOKEN_SECRET is not defined in environment variables"
    );
  }

  try {
    const accessToken = jwt.sign(
      {
        user_id,
        email,
      },
      jwtSecret,
      {
        expiresIn: "15m",
      }
    );

    const refreshToken = jwt.sign(
      {
        user_id,
      },
      refreshSecret,
      { expiresIn: "30d" }
    );

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
  } catch (error) {
    console.error("Error generating JWT:", error);
    throw new Error("Error generating authentication tokens");
  }
};
