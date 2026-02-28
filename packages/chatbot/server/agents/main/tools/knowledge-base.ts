import { MCPClient } from "@ai-sdk/mcp";
import { z } from "zod";

const uploadFileInputSchema = z.object({
  filename: z.string(),
  content: z.string(), // base64
});

const uploadFileOutputSchema = z.object({
  message: z.string(),
  status: z.string(),
});

const indexingStatusInputSchema = z.object({});

const indexingStatusOutputSchema = z.object({
  processing: z.array(z.string()),
  pending: z.array(z.string()),
  finished: z.array(z.string()),
  failed: z.array(z.string()),
});

const searchKnowledgeBaseInputSchema = z.object({
  query: z.string(),
  k: z.number().int().positive().optional(),
});

const searchKnowledgeBaseHitSchema = z.object({
  source: z.string(),
  url: z.string(),
  text: z.string(),
  score: z.number().nullable().optional(),
});

const searchKnowledgeBaseOutputSchema = z.object({
  query: z.string(),
  results: z.array(searchKnowledgeBaseHitSchema),
});

export const knowledgeBaseMcpToolSchemas = {
  upload_file: {
    inputSchema: uploadFileInputSchema,
    outputSchema: uploadFileOutputSchema,
  },
  get_indexing_status: {
    inputSchema: indexingStatusInputSchema,
    outputSchema: indexingStatusOutputSchema,
  },
  search_knowledge_base: {
    inputSchema: searchKnowledgeBaseInputSchema,
    outputSchema: searchKnowledgeBaseOutputSchema,
  },
} as const;

export async function getKnowledgeBaseMcpTool(client: MCPClient) {
  return await client.tools({
    schemas: knowledgeBaseMcpToolSchemas,
  });
}
