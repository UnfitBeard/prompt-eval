// src/models/schemas.ts
import { Schema, model, models, Types } from 'mongoose';

/* =======================
   ENUMS / CONSTANTS
======================= */
export const Domains = ['software', 'education', 'content'] as const;
export type Domain = (typeof Domains)[number];

export const Difficulties = ['Beginner', 'Intermediate', 'Advanced'] as const;
export type Difficulty = (typeof Difficulties)[number];

export const Categories = [
  'code-review',
  'documentation',
  'bug-report',
  'lesson-plan',
  'blog-post',
  'marketing-copy',
  'social-media',
  'email-communication',
] as const;
export type Category = (typeof Categories)[number];

export const Roles = ['admin', 'member'] as const;
export type Role = (typeof Roles)[number];

export const TemplateStatus = ['draft', 'published', 'archived'] as const;
export type TemplateStatus = (typeof TemplateStatus)[number];

export const PromptStatus = ['draft', 'submitted', 'evaluated'] as const;
export type PromptStatus = (typeof PromptStatus)[number];

export const ActivityTypes = [
  'template.created',
  'template.edited',
  'prompt.created',
  'prompt.evaluated',
  'prompt.rewrite.applied',
  'user.login',
  'user.logout',
] as const;
export type ActivityType = (typeof ActivityTypes)[number];

export const AchievementStatus = ['earned', 'in_progress'] as const;
export type AchievementStatus = (typeof AchievementStatus)[number];

/* =======================
   SUBDOCUMENTS
======================= */
const SuggestionSchema = new Schema(
  {
    text: { type: String, required: true, trim: true },
  },
  { _id: false }
);

const ImprovementSchema = new Schema(
  {
    text: { type: String, required: true, trim: true },
  },
  { _id: false }
);

const RewriteSchema = new Schema(
  {
    title: { type: String, required: true, trim: true },
    content: { type: String, required: true, trim: true },
    improvements: { type: [ImprovementSchema], default: [] },
  },
  { _id: false }
);

const ScoreSchema = new Schema(
  {
    clarity: { type: Number, min: 0, max: 10, required: true },
    context: { type: Number, min: 0, max: 10, required: true },
    relevance: { type: Number, min: 0, max: 10, required: true },
    specificity: { type: Number, min: 0, max: 10, required: true },
    creativity: { type: Number, min: 0, max: 10, required: true },
    overall: { type: Number, min: 0, max: 10, required: true },
  },
  { _id: false }
);

const VersionSchema = new Schema(
  {
    number: { type: Number, required: true }, // 1,2,3...
    content: { type: String, required: true },
    notes: { type: String, trim: true },
    createdBy: { type: Schema.Types.ObjectId, ref: 'User', required: true },
    createdAt: { type: Date, default: Date.now },
  },
  { _id: false }
);

/* =======================
   ORGANIZATION
======================= */
export interface IOrganization {
  _id: Types.ObjectId;
  name: string;
  domain?: string;
  plan: 'free' | 'pro' | 'enterprise';
  seatLimit?: number;
}

const OrganizationSchema = new Schema<IOrganization>(
  {
    name: { type: String, required: true, trim: true },
    domain: { type: String, trim: true },
    plan: {
      type: String,
      enum: ['free', 'pro', 'enterprise'],
      default: 'free',
    },
    seatLimit: { type: Number },
  },
  { timestamps: true }
);

export const Organization =
  models.Organization ||
  model<IOrganization>('Organization', OrganizationSchema);

/* =======================
   USER & AUTH
======================= */
export interface IAuthProvider {
  provider: 'google' | 'github';
  providerId: string;
}
const AuthProviderSchema = new Schema<IAuthProvider>(
  {
    provider: { type: String, enum: ['google', 'github'], required: true },
    providerId: { type: String, required: true },
  },
  { _id: false }
);

export interface IUser {
  _id: Types.ObjectId;
  fullName: string;
  email: string;
  passwordHash?: string; // optional if SSO-only
  phone?: string;
  role: Role;
  organization?: Types.ObjectId;
  avatarUrl?: string;
  location?: string;
  employeeId?: string;
  language?: string;
  providers: IAuthProvider[];
  joinedAt: Date;
  lastActiveAt?: Date;
}

const UserSchema = new Schema<IUser>(
  {
    fullName: { type: String, required: true, trim: true },
    email: {
      type: String,
      required: true,
      unique: true,
      index: true,
      lowercase: true,
      trim: true,
    },
    passwordHash: { type: String },
    phone: { type: String },
    role: { type: String, enum: Roles, default: 'member', index: true },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },
    avatarUrl: { type: String },
    location: { type: String },
    employeeId: { type: String },
    language: { type: String, default: 'en' },
    providers: { type: [AuthProviderSchema], default: [] },
    joinedAt: { type: Date, default: Date.now },
    lastActiveAt: { type: Date },
  },
  { timestamps: true }
);

UserSchema.index({ fullName: 'text', email: 'text' });

export const User = models.User || model<IUser>('User', UserSchema);

/* =======================
   TEMPLATE
======================= */
export interface ITemplate {
  _id: Types.ObjectId;
  title: string;
  description?: string;
  domain: Domain;
  category: Category;
  difficulty: Difficulty;
  content: string; // the current active version content
  tags: string[];

  status: TemplateStatus;
  createdBy: Types.ObjectId;
  organization?: Types.ObjectId;

  versions: Types.DocumentArray<any>; // VersionSchema
  stats: {
    uses: number;
    avgScore: number;
  };
}

const TemplateSchema = new Schema<ITemplate>(
  {
    title: { type: String, required: true, trim: true },
    description: { type: String, trim: true },
    domain: { type: String, enum: Domains, required: true, index: true },
    category: { type: String, enum: Categories, required: true, index: true },
    difficulty: { type: String, enum: Difficulties, required: true },
    content: { type: String, required: true },
    tags: { type: [String], default: [], index: true },
    status: {
      type: String,
      enum: TemplateStatus,
      default: 'published',
      index: true,
    },
    createdBy: { type: Schema.Types.ObjectId, ref: 'User', required: true },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },
    versions: { type: VersionSchema.get, default: [] },
    stats: {
      uses: { type: Number, default: 0, index: true },
      avgScore: { type: Number, default: 0 },
    },
  },
  { timestamps: true }
);

TemplateSchema.index({ title: 'text', description: 'text', tags: 'text' });

export const Template =
  models.Template || model<ITemplate>('Template', TemplateSchema);

/* =======================
   PROMPT
======================= */
export interface IPrompt {
  _id: Types.ObjectId;
  user: Types.ObjectId;
  organization?: Types.ObjectId;
  template?: Types.ObjectId;

  originalText: string;
  currentText: string;
  status: PromptStatus; // draft | submitted | evaluated

  // quick denorm for lists
  lastOverallScore?: number; // from last evaluation
  lastEvaluatedAt?: Date;
}

const PromptSchema = new Schema<IPrompt>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },
    template: { type: Schema.Types.ObjectId, ref: 'Template' },

    originalText: { type: String, required: true },
    currentText: { type: String, required: true },
    status: { type: String, enum: PromptStatus, default: 'draft', index: true },

    lastOverallScore: { type: Number },
    lastEvaluatedAt: { type: Date },
  },
  { timestamps: true }
);

PromptSchema.index({ originalText: 'text', currentText: 'text' });

export const Prompt = models.Prompt || model<IPrompt>('Prompt', PromptSchema);

/* =======================
   EVALUATION
======================= */
export interface IEvaluation {
  _id: Types.ObjectId;
  prompt: Types.ObjectId;
  user: Types.ObjectId; // who triggered
  template?: Types.ObjectId;

  modelName?: string; // which LLM evaluated
  scores: {
    clarity: number;
    context: number;
    relevance: number;
    specificity: number;
    creativity: number;
    overall: number;
  };

  suggestions: { text: string }[];
  rewrites: {
    title: string;
    content: string;
    improvements: { text: string }[];
  }[];

  tokensUsed?: number;
  durationMs?: number;
  createdAt: Date;
}

const EvaluationSchema = new Schema<IEvaluation>(
  {
    prompt: {
      type: Schema.Types.ObjectId,
      ref: 'Prompt',
      required: true,
      index: true,
    },
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    template: { type: Schema.Types.ObjectId, ref: 'Template' },

    modelName: { type: String },
    scores: { type: ScoreSchema, required: true },
    suggestions: { type: [SuggestionSchema], default: [] },
    rewrites: { type: [RewriteSchema], default: [] },

    tokensUsed: { type: Number },
    durationMs: { type: Number },
    createdAt: { type: Date, default: Date.now, index: true },
  },
  { timestamps: true }
);

EvaluationSchema.index({ 'scores.overall': -1 });

export const Evaluation =
  models.Evaluation || model<IEvaluation>('Evaluation', EvaluationSchema);

/* =======================
   ACTIVITY (audit/event log)
======================= */
export interface IActivity {
  _id: Types.ObjectId;
  user: Types.ObjectId;
  organization?: Types.ObjectId;
  type: ActivityType;
  // optional foreign refs
  template?: Types.ObjectId;
  prompt?: Types.ObjectId;
  evaluation?: Types.ObjectId;

  meta?: Record<string, any>;
  at: Date;
}

const ActivitySchema = new Schema<IActivity>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },
    type: { type: String, enum: ActivityTypes, required: true, index: true },
    template: { type: Schema.Types.ObjectId, ref: 'Template' },
    prompt: { type: Schema.Types.ObjectId, ref: 'Prompt' },
    evaluation: { type: Schema.Types.ObjectId, ref: 'Evaluation' },
    meta: { type: Schema.Types.Mixed },
    at: { type: Date, default: Date.now, index: true },
  },
  { timestamps: true }
);

ActivitySchema.index({ type: 1, at: -1 });

export const Activity =
  models.Activity || model<IActivity>('Activity', ActivitySchema);

/* =======================
   ACHIEVEMENT
======================= */
export interface IAchievement {
  _id: Types.ObjectId;
  user: Types.ObjectId;
  title: string;
  status: AchievementStatus; // earned | in_progress
  progressPct?: number; // 0..100
  earnedAt?: Date;
}

const AchievementSchema = new Schema<IAchievement>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    title: { type: String, required: true },
    status: { type: String, enum: AchievementStatus, default: 'in_progress' },
    progressPct: { type: Number, min: 0, max: 100 },
    earnedAt: { type: Date },
  },
  { timestamps: true }
);

export const Achievement =
  models.Achievement || model<IAchievement>('Achievement', AchievementSchema);

/* =======================
   USER STATS (for dashboards)
======================= */
export interface IUserStats {
  _id: Types.ObjectId;
  user: Types.ObjectId;
  organization?: Types.ObjectId;

  // cumulative
  totalPrompts: number;
  avgScore: number; // 0..10
  timeInvestedHours: number;
  currentStreakDays: number;

  // rollups by day (for charts)
  daily: {
    date: string; // 'YYYY-MM-DD'
    prompts: number;
    avgScore: number; // 0..10
  }[];
}

const UserStatsSchema = new Schema<IUserStats>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      unique: true,
      index: true,
    },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },

    totalPrompts: { type: Number, default: 0 },
    avgScore: { type: Number, default: 0 },
    timeInvestedHours: { type: Number, default: 0 },
    currentStreakDays: { type: Number, default: 0 },

    daily: {
      type: [
        new Schema(
          {
            date: { type: String, required: true }, // YYYY-MM-DD
            prompts: { type: Number, default: 0 },
            avgScore: { type: Number, default: 0 },
          },
          { _id: false }
        ),
      ],
      default: [],
    },
  },
  { timestamps: true }
);

export const UserStats =
  models.UserStats || model<IUserStats>('UserStats', UserStatsSchema);

/* =======================
   TEMPLATE USAGE (for "Most Used")
======================= */
export interface ITemplateUsage {
  _id: Types.ObjectId;
  template: Types.ObjectId;
  user?: Types.ObjectId; // optional per-user breakdown
  organization?: Types.ObjectId;
  date: string; // YYYY-MM-DD
  count: number;
}

const TemplateUsageSchema = new Schema<ITemplateUsage>(
  {
    template: {
      type: Schema.Types.ObjectId,
      ref: 'Template',
      required: true,
      index: true,
    },
    user: { type: Schema.Types.ObjectId, ref: 'User' },
    organization: { type: Schema.Types.ObjectId, ref: 'Organization' },
    date: { type: String, required: true, index: true },
    count: { type: Number, default: 1 },
  },
  { timestamps: true }
);

TemplateUsageSchema.index({ template: 1, date: -1 });
TemplateUsageSchema.index({ user: 1, date: -1 });

export const TemplateUsage =
  models.TemplateUsage ||
  model<ITemplateUsage>('TemplateUsage', TemplateUsageSchema);

/* =======================
   HANDY VIRTUALS / HOOKS
======================= */
// Keep Prompt.lastOverallScore & lastEvaluatedAt in sync after an evaluation is created.
EvaluationSchema.post('save', async function (doc) {
  const { prompt, scores } = doc as IEvaluation;
  try {
    await Prompt.findByIdAndUpdate(prompt, {
      lastOverallScore: scores.overall,
      lastEvaluatedAt: new Date(),
      status: 'evaluated',
    }).exec();
  } catch (e) {
    // swallow; logging layer can capture if needed
  }
});

// Increment template usage when an evaluation ties to a template.
EvaluationSchema.post('save', async function (doc) {
  const e = doc as IEvaluation;
  if (!e.template) return;
  const day = new Date().toISOString().slice(0, 10);
  await Template.updateOne(
    { _id: e.template },
    {
      $inc: {
        'stats.uses': 1,
        // naive rolling average update; use aggregation for accuracy at scale
        // here we just move avgScore slightly toward new score
      },
    }
  ).exec();
  await TemplateUsage.updateOne(
    { template: e.template, user: e.user, date: day },
    { $inc: { count: 1 } },
    { upsert: true }
  ).exec();
});
