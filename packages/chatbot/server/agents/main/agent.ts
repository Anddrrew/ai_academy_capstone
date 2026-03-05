import { createOpenAI } from "@ai-sdk/openai";
import { devToolsMiddleware } from "@ai-sdk/devtools";
import { ToolLoopAgent, stepCountIs, wrapLanguageModel } from "ai";

import { config } from "@/server/config";
import { MAIN_AGENT_SYSTEM_PROMPT } from "./prompt";
import { createKnowledgeBaseMcpClient } from "@/server/mcp/knowledge-base";
import { createGithubMcpClient } from "@/server/mcp/github";
import { getKnowledgeBaseMcpTool } from "./tools/knowledge-base";
import { getGithubMcpTools } from "./tools/github";
import { createMemoryTools } from "./tools/memory";

const provider = createOpenAI({
  apiKey: config.OPENAI_API_KEY,
});

const model = wrapLanguageModel({
  model: provider.responses(config.OPENAI_CHAT_MODEL),
  middleware: devToolsMiddleware(),
});

export async function createMainAgent(userId: string) {
  console.log(`Creating main agent for user ${userId}`);
  const knowledgeBaseMcpClient = await createKnowledgeBaseMcpClient();
  console.log("Knowledge base MCP client created");
  const knowledgeBaseTools = await getKnowledgeBaseMcpTool(
    knowledgeBaseMcpClient,
  );
  console.log("Knowledge base tools created");

  const githubMcpClient = await createGithubMcpClient();
  console.log("GitHub MCP client created");
  const githubTools = await getGithubMcpTools(githubMcpClient);
  console.log("GitHub tools created");

  const memoryTools = createMemoryTools(userId);
  console.log("Memory tools created");
  const tools = { ...knowledgeBaseTools, ...githubTools, ...memoryTools };
  const toolsMeta = Object.entries(tools).map(([name, t]) => ({
    name,
    description: (t as { description?: string }).description ?? name,
  }));
  const agent = new ToolLoopAgent({
    model,
    instructions: MAIN_AGENT_SYSTEM_PROMPT,
    stopWhen: stepCountIs(5),
    tools,
    providerOptions: {
      openai: {
        reasoningEffort: "medium",
        reasoningSummary: "auto",
      },
    },
    onFinish: () => {
      knowledgeBaseMcpClient.close();
      githubMcpClient.close();
    },
  });
  return { agent, toolsMeta };
}
