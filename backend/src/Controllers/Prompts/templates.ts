import express, { Request, Response, NextFunction } from 'express';
import dotenv from 'dotenv';
import { Schema } from 'mongoose';
import { Template, ITemplate } from '../../Models/Schema';

dotenv.config();

export const addTemplate = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const {
    title,
    description,
    category,
    createdBy,
    difficulty,
    domain,
    prompt,
  } = req.body;
  if (!prompt || !difficulty || !domain || !category) {
    return res.status(200).json({
      message: 'Missing Prompt values',
    });
  }

  try {
  } catch (error) {
    console.error('Error while creating template: ', error);
    res.status(500).json({ message: 'Internal Server Error' });
  }
  const newTemplate = new Template({
    title,
    description,
    domain,
    category,
    difficulty,
    content: prompt,
    createdBy: '68d010116ef123ecc581d9a7',
  });

  await newTemplate.save();
  res.status(201).json({
    message: 'Template Created successfully',
    prompt: {
      domain: newTemplate._id,
      category: newTemplate.category,
      difficulty: newTemplate.difficulty,
      content: newTemplate.content,
    },
  });
};

export const getTemplates = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const templates = await Template.find({});

  if (!templates) {
    return res.status(404).json({ message: 'No templates in DB' });
  }

  return res.status(200).json({
    message: 'Successfully retrieved the prompts',
    templates: templates,
  });
};
