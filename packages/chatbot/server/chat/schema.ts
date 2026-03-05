import { z } from "zod";

export const chatRequestSchema = z.object({
  messages: z.array(z.unknown()),
  userId: z.string().min(1).default("default_user"),
});

export type ChatRequestBody = z.infer<typeof chatRequestSchema>;
