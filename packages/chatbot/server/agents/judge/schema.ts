import { z } from "zod";

export const evaluationFeedbackSchema = z.object({
  score: z.enum(["pass", "needs_improvement", "fail"]),
  feedback: z.string().min(1),
});

export type EvaluationFeedback = z.infer<typeof evaluationFeedbackSchema>;
