import { createMCPClient } from "@ai-sdk/mcp";
import { config } from "@/server/config";

export async function createGithubMcpClient() {
  return createMCPClient({
    transport: {
      type: "http",
      url: "https://api.githubcopilot.com/mcp/",
      headers: {
        Authorization: `Bearer ${config.github.token}`,
        "X-MCP-Toolsets": "git,repos,users",
        "X-MCP-Readonly": "true",
      },
    },
  });
}
