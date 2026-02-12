import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { CourseService } from '../../../Service/course.service';

type CourseDifficulty = 'beginner' | 'intermediate' | 'advanced';

interface ModuleQuestion {
  id: string;
  prompt: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

interface CourseModule {
  id: string;
  title: string;
  summary: string; // short_summary from your JSON
  lessonMarkdown?: string; // full lesson_markdown from your JSON
  duration?: string;
  focus?: string;
  points: number;
  question: ModuleQuestion;
  backendLessonId?: string; // optional, for backend linking later
}

interface Course {
  id: 'basics' | 'rag' | 'advanced';
  title: string;
  subtitle: string;
  difficulty: CourseDifficulty;
  estimatedHours: number;
  audience: string;
  badge?: string;
  primaryColor: string;
  keyTopics: string[];
  outcomes: string[];
  modules: CourseModule[];
}

// Reusable question templates so every module has a practice MCQ
const BASIC_Q_FOUNDATIONS: ModuleQuestion = {
  id: 'basic-foundations',
  prompt:
    'What is the primary goal of prompt engineering when working with large language models (LLMs)?',
  options: [
    'To modify the internal weights of the model',
    'To design clear instructions and context so the model produces reliable outputs',
    'To reduce the size of the model so it runs faster',
    'To replace the training data of the model with new documents',
  ],
  correctIndex: 1,
  explanation:
    'Prompt engineering focuses on how you communicate with an LLM—through instructions, context, and examples—so that its outputs become more reliable and useful, without changing the model itself.',
};

const BASIC_Q_ANATOMY: ModuleQuestion = {
  id: 'basic-anatomy',
  prompt:
    'Which of the following is NOT typically considered a core building block of a well‑structured prompt?',
  options: [
    'Clear instructions',
    'Relevant context',
    'Input data or question',
    'GPU type used to host the model',
  ],
  correctIndex: 3,
  explanation:
    'A prompt usually consists of instructions, context, and input/output guidance. Hardware details like GPU type are generally irrelevant to the prompt itself.',
};

const BASIC_Q_ITERATION: ModuleQuestion = {
  id: 'basic-iteration',
  prompt:
    'Why is an iterative “try → observe → tweak” loop important in prompt engineering?',
  options: [
    'Because prompts always work perfectly on the first try',
    'Because it lets you gradually refine prompts based on real outputs and failures',
    'Because LLMs can only be queried a fixed number of times',
    'Because it guarantees 100% accuracy for all tasks',
  ],
  correctIndex: 1,
  explanation:
    'An iterative loop helps you learn from the model’s behavior and refine prompts step by step. It improves quality but never guarantees perfection.',
};

const RAG_Q_ARCH: ModuleQuestion = {
  id: 'rag-arch',
  prompt:
    'In a RAG (Retrieval‑Augmented Generation) system, what role does retrieval play?',
  options: [
    'It trains the base model from scratch',
    'It brings in relevant external documents to ground the model’s answer',
    'It compresses the model’s parameters to save memory',
    'It replaces the need for a language model entirely',
  ],
  correctIndex: 1,
  explanation:
    'Retrieval pulls relevant documents or chunks from an external knowledge source so that the model can generate answers grounded in that context.',
};

const RAG_Q_GROUNDED: ModuleQuestion = {
  id: 'rag-grounded',
  prompt:
    'Which prompting pattern best encourages grounded, citation‑rich answers in a RAG system?',
  options: [
    '“Answer from your general knowledge only.”',
    '“Ignore the context and be creative.”',
    '“Answer only using the provided context. If the answer is not present, say you don’t know, and cite the source documents you used.”',
    '“Always give an answer, even if the context is empty.”',
  ],
  correctIndex: 2,
  explanation:
    'Explicitly telling the model to answer only from context, refuse when evidence is missing, and cite sources supports grounded answers and discourages hallucinations.',
};

const ADV_Q_COT: ModuleQuestion = {
  id: 'adv-cot',
  prompt:
    'What is a key benefit of Chain‑of‑Thought (CoT) prompting for complex reasoning tasks?',
  options: [
    'It hides all intermediate reasoning from the model',
    'It forces the model to answer in a single token',
    'It encourages the model to break the problem into smaller steps, which often improves correctness',
    'It guarantees faster inference for every query',
  ],
  correctIndex: 2,
  explanation:
    'CoT prompts ask the model to reason step by step, which tends to improve correctness on complex tasks even if it can be slower or more verbose.',
};

const ADV_Q_SELF_CORRECT: ModuleQuestion = {
  id: 'adv-self-correct',
  prompt:
    'Self‑correction prompts typically ask the model to do which of the following?',
  options: [
    'Randomly change its answer',
    'Ignore previous reasoning steps',
    'Critique its own answer and revise it if needed',
    'Stop generating any output',
  ],
  correctIndex: 2,
  explanation:
    'Self‑correction patterns ask the model to review, critique, and potentially revise its prior answer, often catching simple errors.',
};

@Component({
  selector: 'app-course-list',
  imports: [CommonModule],
  templateUrl: './course-list.component.html',
  styleUrls: ['./course-list.component.css'],
})
export class CourseListComponent implements OnInit {
  constructor(private courseService: CourseService) {}

  ngOnInit(): void {
    this.loadCourses();
  }

  private loadCourses(): void {
    this.courseService.getAcademyCourses().subscribe({
      next: (courses: any[]) => {
        console.log('[CourseListComponent] academy courses:', courses);

        // Shape matches the local Course interface; just assign.
        this.courses = (courses ?? []) as Course[];
        console.log('[CourseListComponent] courses assigned:', this.courses);
      },
      error: (err) => {
        console.error('Failed to load academy courses', err);
      },
    });
  }
  // return 1-based module index or '–' if not found
  getModulePosition(course: Course, moduleId: string): number | string {
    const idx = course.modules.findIndex((mod) => mod.id === moduleId);
    return idx >= 0 ? idx + 1 : '–';
  }

  /**
   * Very lightweight markdown cleaner so lessonMarkdown can be shown as readable text
   * without raw markers like ##, **, backticks, etc.
   */
  cleanMarkdown(text?: string | null): string {
    if (!text) {
      return '';
    }

    let cleaned = text;

    // Strip fenced code block markers but keep inner text
    cleaned = cleaned.replace(/```/g, '');

    // Remove markdown headings (##, ###, etc.)
    cleaned = cleaned.replace(/^#{1,6}\s*/gm, '');

    // Bold and italics: **text**, *text*, _text_
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1');
    cleaned = cleaned.replace(/\*(.*?)\*/g, '$1');
    cleaned = cleaned.replace(/_(.*?)_/g, '$1');

    // Inline code: `code`
    cleaned = cleaned.replace(/`([^`]+)`/g, '$1');

    // Links: [text](url) -> text
    cleaned = cleaned.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1');

    // Blockquotes: > text
    cleaned = cleaned.replace(/^>\s?/gm, '');

    // Collapse 3+ blank lines into at most 2
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

    return cleaned.trim();
  }

  courses: Course[] = [];

  // Current course selection in the main page
  selectedCourseId: Course['id'] = 'basics';

  // Learning mode overlay state
  activeCourseId: Course['id'] | null = null;
  activeModule: CourseModule | null = null;
  isLearningModeOpen = false;

  // XP & badges (client‑side; can be backed by server data)
  totalPoints = 0;
  earnedBadges: string[] = [];

  // Per‑module progress & answers
  private moduleProgress = new Map<
    string,
    {
      completed: boolean;
      pointsAwarded: number;
      lastResult?: 'correct' | 'incorrect';
    }
  >();
  private moduleAnswers = new Map<string, number | null>();

  get selectedCourse(): Course | undefined {
    return this.courses.find((c) => c.id === this.selectedCourseId);
  }

  getActiveCourse(): Course | undefined {
    if (!this.activeCourseId) return undefined;
    return this.courses.find((c) => c.id === this.activeCourseId);
  }

  // --- Course selection (list view) ---

  selectCourse(id: Course['id']): void {
    this.selectedCourseId = id;

    // If overlay is open for a different course, close it
    if (
      this.isLearningModeOpen &&
      this.activeCourseId &&
      this.activeCourseId !== id
    ) {
      this.closeLearningMode();
    }
  }

  // --- Open / close learning mode overlay ---

  openModule(course: Course, module: CourseModule): void {
    this.selectedCourseId = course.id;
    this.activeCourseId = course.id;
    this.activeModule = module;
    this.isLearningModeOpen = true;

    if (!this.moduleAnswers.has(module.id)) {
      this.moduleAnswers.set(module.id, null);
    }
  }

  closeLearningMode(): void {
    this.isLearningModeOpen = false;
    this.activeModule = null;
    this.activeCourseId = null;
  }

  // --- Progression gating (Next module) ---

  getNextModuleInCourse(
    course: Course,
    module: CourseModule
  ): CourseModule | null {
    const index = course.modules.findIndex((m) => m.id === module.id);
    if (index === -1) return null;
    if (index < course.modules.length - 1) {
      return course.modules[index + 1];
    }
    return null;
  }

  canGoNext(): boolean {
    if (!this.activeModule || !this.activeCourseId) return false;
    const course = this.getActiveCourse();
    if (!course) return false;
    const progress = this.getModuleProgress(this.activeModule.id);
    const next = this.getNextModuleInCourse(course, this.activeModule);
    return progress.completed && !!next;
  }

  goToNextModule(): void {
    if (!this.activeModule || !this.activeCourseId) return;
    const course = this.getActiveCourse();
    if (!course) return;

    const next = this.getNextModuleInCourse(course, this.activeModule);
    if (!next) {
      // No more modules in this course; close overlay
      this.closeLearningMode();
      return;
    }

    this.activeModule = next;
    // Reset selection for next module
    if (!this.moduleAnswers.has(next.id)) {
      this.moduleAnswers.set(next.id, null);
    } else {
      this.moduleAnswers.set(next.id, null);
    }
  }

  // --- Utility / display helpers ---

  trackByCourseId(_: number, course: Course): string {
    return course.id;
  }

  trackByModuleId(_: number, module: CourseModule): string {
    return module.id;
  }

  getDifficultyLabel(difficulty: CourseDifficulty): string {
    switch (difficulty) {
      case 'beginner':
        return 'Beginner';
      case 'intermediate':
        return 'Intermediate';
      case 'advanced':
        return 'Advanced';
      default:
        return difficulty;
    }
  }

  getDifficultyBadgeClasses(difficulty: CourseDifficulty): string {
    if (difficulty === 'beginner') {
      return 'bg-green-100 text-green-800';
    }
    if (difficulty === 'intermediate') {
      return 'bg-amber-100 text-amber-800';
    }
    return 'bg-rose-100 text-rose-800';
  }

  formatHours(hours: number): string {
    if (hours <= 1) return `${hours} hour`;
    return `${hours} hours`;
  }

  // --- Module progress & XP ---

  getModuleProgress(moduleId: string) {
    const entry = this.moduleProgress.get(moduleId);
    return (
      entry ?? {
        completed: false,
        pointsAwarded: 0,
        lastResult: undefined as 'correct' | 'incorrect' | undefined,
      }
    );
  }

  selectAnswer(module: CourseModule, optionIndex: number): void {
    this.moduleAnswers.set(module.id, optionIndex);
  }

  getSelectedAnswerIndex(module: CourseModule): number | null {
    return this.moduleAnswers.get(module.id) ?? null;
  }

  submitAnswer(module: CourseModule): void {
    const selectedIndex = this.moduleAnswers.get(module.id);
    if (selectedIndex == null) return;

    const isCorrect = selectedIndex === module.question.correctIndex;
    const existing = this.getModuleProgress(module.id);

    // XP mechanism:
    // - Fixed base XP per module (module.points)
    // - Awarded only once, on first correct completion
    if (isCorrect && !existing.completed) {
      const gained = module.points;
      this.totalPoints += gained;

      this.moduleProgress.set(module.id, {
        completed: true,
        pointsAwarded: gained,
        lastResult: 'correct',
      });

      // Sync XP with backend so the main dashboard reflects progress.
      // This uses a lightweight /progress/xp endpoint and does not yet
      // depend on real Lesson documents in Mongo.
      this.courseService.addXp(gained, `xp-mode:${module.id}`).subscribe({
        // We don't currently need the returned total_xp, but you could
        // propagate it into a shared store if you want real-time
        // dashboard updates.
        next: () => {},
        error: (err) => {
          // Fail silently for the user; log for debugging.
          console.error('Failed to sync XP with backend', err);
        },
      });

      this.recomputeBadges();
    } else {
      this.moduleProgress.set(module.id, {
        ...existing,
        lastResult: isCorrect ? 'correct' : 'incorrect',
      });
    }
  }

  private recomputeBadges(): void {
    const badges: string[] = [];

    // Example tiers – you can align names with backend achievements:
    if (this.totalPoints >= 50) {
      badges.push('Beginner Prompt Engineer');
    }
    if (this.totalPoints >= 150) {
      badges.push('Prompt Engineering Practitioner');
    }
    if (this.totalPoints >= 250) {
      badges.push('RAG Master');
    }
    if (this.totalPoints >= 400) {
      badges.push('Advanced Prompt Architect');
    }

    this.earnedBadges = badges;
  }
}
