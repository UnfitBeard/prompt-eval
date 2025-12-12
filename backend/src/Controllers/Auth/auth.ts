import express from 'express';
import dotenv from 'dotenv';
import { Request, Response, NextFunction } from 'express';
import { Collection, Db } from 'mongodb';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { generateToken } from '../../Utils/Helpers/generateToken';
import mongoose from 'mongoose';
import axios from 'axios';
import { IUser, User } from '../../Models/Schema';
dotenv.config();

export const registration = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const { fullName, email, password } = req.body;
  console.log('registration: ', email);

  if (!fullName || !password || !email) {
    console.log('Error: Missing credentials');
    return res.status(400).json({ message: 'Missing credentials.' });
  }

  try {
    const existingUser = await User.findOne({ email });
    if (existingUser)
      return res.status(400).json({ message: 'User already registered' });
    const passwordHash = bcrypt.hashSync(password, 10);

    const newUser = new User({
      fullName,
      email,
      passwordHash,
    });

    await newUser.save();

    const tokens = await generateToken(res, newUser._id, newUser.email);

    console.log('Successful registration for: ', email);

    res.status(201).json({
      message: 'User created successfully',
      user: {
        id: newUser._id,
        email: newUser.email,
        fullName: newUser.fullName,
        // organization: newUser.organization,
      },
      token: tokens,
    });
  } catch (error) {
    console.error('Error: ', error);
    res.status(500).json({
      message: 'Internal server error',
    });
  }
};

export const login = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const { email, password } = req.body;

  if (!email || !password) {
    console.log('Error: Missing email or password in login request');

    return res
      .status(400)
      .json({ message: 'Email and password are required.' });
  }

  try {
    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({ message: 'Invalid credentials.' });
    }

    const passwordIsTrue = bcrypt.compareSync(password, user.passwordHash);

    if (!passwordIsTrue) {
      return res.status(401).json({
        message: 'Wrong credentials',
      });
    }

    const tokens = await generateToken(res, user._id, user.email);

    return res.status(200).json({
      message: 'Login successful',
      user: {
        id: user._id,
        email: user.email,
        fullName: user.fullName,
      },
      token: tokens,
    });
  } catch (error) {
    console.error('Error during login:', error);
    return res.status(500).json({ message: 'Internal server error.' });
  }
};

export const githubAuthRedirect = async (_req: Request, res: Response) => {
  const redirectUrl = 'http://localhost:10000/api/v1/auth/githubAuth';
  const clientId = process.env.GITHUB_CLIENT_ID;

  const url = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUrl}&scope=user:email`;
  res.redirect(url);
};
