import { z } from "zod";

export const qdrantCollections = {
  memory: "user_memory",
  evaluation: "judge_evaluations",
} as const;

const GITHUB_OWNER = "Anddrrew";
const GITHUB_REPO = "ai_academy_capstone";

// Schema with defaults on every field so parsing never throws.
// Missing env vars produce warnings, not crashes.
const configSchema = z.object({
  qdrant: z.object({
    url: z.string().default(""),
  }),
  embedding: z.object({
    publicUrl: z.string().default(""),
    vectorSize: z.coerce.number().int().positive().default(1024),
  }),
  openAI: z.object({
    apiKey: z.string().default(""),
    chatModel: z.string().default("gpt-5.2"),
    codeExplorerModel: z.string().default("gpt-5.3-codex"),
    judgeModel: z.string().default("gpt-5.2"),
  }),
  knowledgeBase: z.object({
    publicUrl: z.string().default(""),
    mcpUrl: z.string().default(""),
  }),
  github: z.object({
    token: z.string().default(""),
    owner: z.string().default(GITHUB_OWNER),
    repo: z.string().default(GITHUB_REPO),
  }),

  MEMORY_TOP_K: z.coerce.number().int().positive().default(5),
});

// Warn about missing required env vars (won't throw)
const REQUIRED_ENV = {
  QDRANT__URL: process.env.QDRANT__URL,
  EMBEDDING__PUBLIC_URL: process.env.EMBEDDING__PUBLIC_URL,
  OPENAI__API_KEY: process.env.OPENAI__API_KEY,
  KNOWLEDGE_BASE__PUBLIC_URL: process.env.KNOWLEDGE_BASE__PUBLIC_URL,
  KNOWLEDGE_BASE__MCP_URL: process.env.KNOWLEDGE_BASE__MCP_URL,
  GITHUB__TOKEN: process.env.GITHUB__TOKEN,
} as const;

const missingVars = Object.entries(REQUIRED_ENV)
  .filter(([, v]) => !v)
  .map(([k]) => k);

if (missingVars.length > 0) {
  console.warn(
    `⚠️  Missing env vars: ${missingVars.join(", ")}\n` +
      `   This is expected during build. They must be set at runtime.`,
  );
}

export type Config = z.infer<typeof configSchema>;

export const config: Config = configSchema.parse({
  qdrant: { url: process.env.QDRANT__URL },
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
