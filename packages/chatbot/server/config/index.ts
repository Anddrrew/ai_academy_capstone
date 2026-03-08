import { z } from "zod";

export const qdrantCollections = {
  memory: "user_memory",
  evaluation: "judge_evaluations",
} as const;

const GITHUB_OWNER = "Anddrrew";
const GITHUB_REPO = "ai_academy_capstone";

const configSchema = z.object({
  qdrant: z.object({
    url: z.url(),
  }),
  embedding: z.object({
    publicUrl: z.url(),
    vectorSize: z.coerce.number().int().positive().default(1024),
  }),
  openAI: z.object({
    apiKey: z.string().min(1),
    chatModel: z.string().min(1).default("gpt-5.2"),
    codeExplorerModel: z.string().min(1).default("gpt-5.3-codex"),
    judgeModel: z.string().min(1).default("gpt-5.2"),
  }),
  knowledgeBase: z.object({
    publicUrl: z.url(),
    mcpUrl: z.url(),
  }),
  github: z.object({
    token: z.string().min(1),
    owner: z.string().min(1).default(GITHUB_OWNER),
    repo: z.string().min(1).default(GITHUB_REPO),
  }),

  MEMORY_TOP_K: z.coerce.number().int().positive().default(5),
});

export const config = configSchema.parse({
  qdrant: {
    url: process.env.QDRANT__URL,
  },
  embedding: {
    publicUrl: process.env.EMBEDDING__PUBLIC_URL,
    vectorSize: process.env.EMBEDDING__VECTOR_SIZE,
  },
  MEMORY_TOP_K: process.env.MEMORY_TOP_K,
  openAI: {
    apiKey: process.env.OPENAI__API_KEY,
    chatModel: process.env.OPENAI__CHAT_MODEL,
    codeExplorerModel: process.env.OPENAI__CODE_EXPLORER_MODEL,
    judgeModel: process.env.OPENAI__JUDGE_MODEL,
  },
  knowledgeBase: {
    publicUrl: process.env.KNOWLEDGE_BASE__PUBLIC_URL,
    mcpUrl: process.env.KNOWLEDGE_BASE__MCP_URL,
  },
  github: {
    token: process.env.GITHUB__TOKEN,
  },
});
