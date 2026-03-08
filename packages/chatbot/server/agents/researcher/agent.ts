import { createOpenAI } from "@ai-sdk/openai";
import { generateText, ToolLoopAgent, stepCountIs } from "ai";

import { config } from "@/server/config";
import { CODEBASE_RESEARCHER_SYSTEM_PROMPT } from "./prompt";
import { createGithubMcpClient } from "@/server/mcp/github";
import { getGithubMcpTools } from "./tools/github";

const provider = createOpenAI({
  apiKey: config.openAI.apiKey,
});

export async function runCodebaseResearchAgent(
  owner: string,
  repo: string,
  query: string,
): Promise<string> {
  console.log(
    `[researcher] starting research for ${owner}/${repo}: "${query}"`,
  );
  const githubMcpClient = await createGithubMcpClient();
  console.log("[researcher] GitHub MCP client connected");

  try {
    const githubTools = await getGithubMcpTools(githubMcpClient);
    const toolNames = Object.keys(githubTools);
    console.log(
      `[researcher] loaded ${toolNames.length} tools: ${toolNames.join(", ")}`,
    );

    const agent = new ToolLoopAgent({
      model: provider.responses(config.openAI.codeExplorerModel),
      instructions: CODEBASE_RESEARCHER_SYSTEM_PROMPT,
      stopWhen: stepCountIs(25),
      tools: githubTools,
      providerOptions: {
        openai: {
          reasoningEffort: "medium",
          reasoningSummary: "auto",
        },
      },
    });

    const prompt = `Repository: ${owner}/${repo}\n\nQuery: ${query}`;
    console.log(`[researcher] sending prompt to agent`);
    const result = await agent.generate({ prompt });

    for (const [i, step] of result.steps.entries()) {
      console.log(
        `[researcher] step ${i + 1}: finishReason=${step.finishReason}`,
      );
      for (const tc of step.toolCalls) {
        const args = "args" in tc ? tc.args : "input" in tc ? tc.input : {};
        console.log(
          `[researcher]   tool: ${tc.toolName}(${JSON.stringify(args).slice(0, 200)})`,
        );
      }
      for (const tr of step.toolResults) {
        const output =
          "result" in tr ? tr.result : "output" in tr ? tr.output : tr;
        console.log(
          `[researcher]   result[${tr.toolName}]: ${JSON.stringify(output).slice(0, 300)}`,
        );
      }
      if (step.text) {
        console.log(`[researcher]   text: ${step.text.slice(0, 200)}`);
      }
    }

    console.log(
      `[researcher] agent finished — steps: ${result.steps.length}, text length: ${result.text.length}, finishReason: ${result.finishReason}`,
    );

    // If the agent hit the step limit without producing text,
    // do a final call without tools to force a summary
    if (!result.text) {
      console.warn(
        "[researcher] hit step limit without text — forcing summary",
      );
      const summaryResult = await generateText({
        model: provider.responses(config.openAI.codeExplorerModel),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        messages: (result as any).messages ?? [],
        system:
          "You have gathered research data above. Now produce a concise summary answering the original query. No more tool calls — just summarize what you found.",
      });
      console.log(
        `[researcher] forced summary length: ${summaryResult.text.length}`,
      );
      return summaryResult.text;
    }

    return result.text;
  } catch (error) {
    console.error("[researcher] agent error:", error);
    throw error;
  } finally {
    githubMcpClient.close();
    console.log("[researcher] GitHub MCP client closed");
  }
}
