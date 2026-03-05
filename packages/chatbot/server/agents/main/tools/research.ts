import { tool } from "ai";
import { z } from "zod";
import { config } from "@/server/config";
import { runCodebaseResearchAgent } from "@/server/agents/researcher";

export const researchCodebaseTool = tool({
  description:
    "Research a GitHub repository using a sub-agent. " +
    "Use this for questions about code architecture, implementation, or design decisions. " +
    "Defaults to this project's own repository if owner/repo are not provided. " +
    "The sub-agent reads files and searches code in its own context, returning a concise summary.",
  inputSchema: z.object({
    query: z
      .string()
      .describe(
        "The research query. Be specific about what information is needed from the codebase.",
      ),
    owner: z
      .string()
      .optional()
      .describe("GitHub repository owner. Defaults to this project's owner."),
    repo: z
      .string()
      .optional()
      .describe("GitHub repository name. Defaults to this project's repo."),
  }),
  execute: async ({ query, owner, repo }) => {
    const resolvedOwner = owner ?? config.GITHUB_OWNER;
    const resolvedRepo = repo ?? config.GITHUB_REPO;
    const summary = await runCodebaseResearchAgent(
      resolvedOwner,
      resolvedRepo,
      query,
    );
    return { summary };
  },
});
