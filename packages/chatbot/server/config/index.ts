import { z } from "zod";

export const qdrantCollections = {
  memory: "user_memory",
  evaluation: "judge_evaluations",
} as const;

const configSchema = z.object({
  QDRANT_URL: z.url(),
  EMBEDDER_URL: z.url(),
  KNOWLEDGE_BASE_MCP_URL: z.url(),
  OPENAI_API_KEY: z.string().min(1),
  OPENAI_CHAT_MODEL: z.string().min(1).default("gpt-5.2"),
  OPENAI_JUDGE_MODEL: z.string().min(1).default("gpt-5.2"),
  MEMORY_TOP_K: z.coerce.number().int().positive().default(5),
  EMBEDDING_VECTOR_SIZE: z.coerce.number().int().positive().default(1024),
});

export const config = configSchema.parse({
  EMBEDDER_URL: process.env.EMBEDDER_URL,
  EMBEDDING_VECTOR_SIZE: process.env.EMBEDDING_VECTOR_SIZE,
  KNOWLEDGE_BASE_MCP_URL: process.env.KNOWLEDGE_BASE_MCP_URL,
  MEMORY_TOP_K: process.env.MEMORY_TOP_K,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  OPENAI_CHAT_MODEL: process.env.OPENAI_CHAT_MODEL,
  OPENAI_JUDGE_MODEL: process.env.OPENAI_JUDGE_MODEL,
  QDRANT_URL: process.env.QDRANT_URL,
});
