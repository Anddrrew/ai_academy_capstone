import { MCPClient } from "@ai-sdk/mcp";

export async function getGithubMcpTools(client: MCPClient) {
  return await client.tools();
}
