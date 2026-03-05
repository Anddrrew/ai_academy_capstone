import { createMCPClient } from "@ai-sdk/mcp";
import { config } from "@/server/config";

export async function createKnowledgeBaseMcpClient() {
  return createMCPClient({
    transport: {
      type: "sse",
      url: config.KNOWLEDGE_BASE_MCP_URL,
    },
  });
}
