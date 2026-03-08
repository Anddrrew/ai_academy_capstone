import { tool } from "ai";
import { z } from "zod";
import { loadSkillContent, type SkillMetadata } from "./discover";

/**
 * Create a load_skill tool that reads the full SKILL.md instructions into context.
 * The agent calls this when it detects a task matching a skill description.
 */
export function createLoadSkillTool(skills: SkillMetadata[]) {
  return tool({
    description:
      "Load specialized instructions for a specific skill. " +
      "Call this BEFORE starting a task that matches a skill description. " +
      "The skill provides detailed rules and workflows you must follow.",
    inputSchema: z.object({
      name: z
        .string()
        .describe(
          "The skill name to load (e.g. 'content-creation', 'knowledge-base-qa')",
        ),
    }),
    execute: async ({ name }) => {
      console.log(`[skills] Loading skill: ${name}`);
      const result = await loadSkillContent(skills, name);
      if ("error" in result) {
        console.warn(`[skills] Skill not found: ${name}`);
        return { error: result.error };
      }
      console.log(
        `[skills] Loaded skill '${name}' (${result.content.length} chars) from ${result.skillDirectory}`,
      );
      return {
        instructions: result.content,
        skillDirectory: result.skillDirectory,
      };
    },
  });
}
