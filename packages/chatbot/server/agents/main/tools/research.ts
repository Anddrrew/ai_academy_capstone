import { tool } from "ai";
import { z } from "zod";
import { config } from "@/server/config";
import { runCodebaseResearchAgent } from "@/server/agents/researcher";

export const researchCodebaseTool = tool({
  description:
    "Research a GitHub repository using a sub-agent. " +
    "Use this for questions about code architecture, implementation, or design decisions. " +
    "The sub-agent reads files and searches code in its own context, returning a concise summary.",
  inputSchema: z.object({
    query: z
      .string()
      .describe(
        "The research query. Be specific about what information is needed from the codebase.",
      ),
    owner: z.string().describe("GitHub repository owner"),
    repo: z.string().describe("GitHub repository name. "),
  }),
  execute: async ({ query, owner, repo }) => {
    const summary = await runCodebaseResearchAgent(owner, repo, query);
    return { summary };
  },
});
