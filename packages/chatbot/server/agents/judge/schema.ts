import { z } from "zod";

const criterionScore = z.enum(["pass", "needs_improvement", "fail"]);

export const evaluationFeedbackSchema = z.object({
  score: z.enum(["pass", "needs_improvement", "fail"]),
  feedback: z.string().min(1),
  criteria: z.object({
    grounding: criterionScore,
    relevance: criterionScore,
    hallucination: criterionScore,
    tool_usage: criterionScore,
  }),
  issues: z.array(z.string()),
});

export type EvaluationFeedback = z.infer<typeof evaluationFeedbackSchema>;
