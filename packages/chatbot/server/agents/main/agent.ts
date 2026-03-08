import { createOpenAI } from "@ai-sdk/openai";
import { ToolLoopAgent, stepCountIs } from "ai";
import { join } from "node:path";

import { config } from "@/server/config";
import { buildMainAgentPrompt } from "./prompt";
import { createKnowledgeBaseMcpClient } from "@/server/mcp/knowledge-base";
import { getKnowledgeBaseTools } from "./tools/knowledge-base";
import { createMemoryTools } from "./tools/memory";
import { researchCodebaseTool } from "./tools/research";
import {
  discoverSkills,
  buildSkillsPrompt,
  createLoadSkillTool,
} from "@/server/skills";

const provider = createOpenAI({
  apiKey: config.openAI.apiKey,
});

const model = provider.responses(config.openAI.chatModel);
const SKILLS_DIRECTORIES = [join(process.cwd(), "server", "skills")];

export async function createMainAgent(userId: string) {
  console.log(`Creating main agent for user ${userId}`);

  // Discover skills at startup
  const skills = await discoverSkills(SKILLS_DIRECTORIES);
  console.log(
    `[skills] Discovered ${skills.length} skills: ${skills.map((s) => s.name).join(", ")}`,
  );

  const knowledgeBaseMcpClient = await createKnowledgeBaseMcpClient();
  console.log("Knowledge base MCP client created");
  const knowledgeBaseTools = await getKnowledgeBaseTools(
    knowledgeBaseMcpClient,
  );
  console.log("Knowledge base tools created");

  const memoryTools = createMemoryTools(userId);
  console.log("Memory tools created");

  const loadSkillTool = createLoadSkillTool(skills);

  const tools = {
    ...knowledgeBaseTools,
    ...memoryTools,
    research_codebase: researchCodebaseTool,
    load_skill: loadSkillTool,
  };
  const toolsMeta = Object.entries(tools).map(([name, t]) => ({
    name,
    description: (t as { description?: string }).description ?? name,
  }));

  // Build system prompt with skills section
  const skillsSection = buildSkillsPrompt(skills);
  const systemPrompt = buildMainAgentPrompt(skillsSection);

  const agent = new ToolLoopAgent({
    model,
    instructions: systemPrompt,
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
    },
  });
  return { agent, toolsMeta };
}
