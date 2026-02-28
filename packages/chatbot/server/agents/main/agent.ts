import { createOpenAI } from "@ai-sdk/openai";
import { devToolsMiddleware } from "@ai-sdk/devtools";
import { ToolLoopAgent, stepCountIs, wrapLanguageModel } from "ai";

import { config } from "@/server/config";
import { MAIN_AGENT_SYSTEM_PROMPT } from "./prompt";
import { createKnowledgeBaseMcpClient } from "@/server/mcp/knowledge-base";
import { getKnowledgeBaseMcpTool } from "./tools/knowledge-base";
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
  const memoryTools = createMemoryTools(userId);
  console.log("Memory tools created");
  return new ToolLoopAgent({
    model,
    instructions: MAIN_AGENT_SYSTEM_PROMPT,
    stopWhen: stepCountIs(5),
    tools: {
      ...knowledgeBaseTools,
      ...memoryTools,
    },
    providerOptions: {
      openai: {
        reasoningEffort: "high",
        reasoningSummary: "auto",
      },
    },
    onFinish: () => knowledgeBaseMcpClient.close(),
  });
}
