import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

export interface SkillMetadata {
  name: string;
  description: string;
  path: string;
}

const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;

/**
 * Parse YAML frontmatter from a SKILL.md file.
 * Supports single-line and multiline (> / |) values.
 */
function parseFrontmatter(content: string): {
  name: string;
  description: string;
} {
  const match = content.match(FRONTMATTER_RE);
  if (!match?.[1]) throw new Error("No frontmatter found");

  const data: Record<string, string> = {};
  let key = "";
  let value = "";

  for (const line of match[1].split("\n")) {
    const kv = line.match(/^(\w[\w-]*):\s*(.*)$/);
    if (kv) {
      if (key) data[key] = value.trim();
      key = kv[1];
      value = kv[2] === ">" || kv[2] === "|" ? "" : kv[2];
    } else if (key && /^\s+/.test(line)) {
      value += " " + line.trim();
    }
  }
  if (key) data[key] = value.trim();

  if (!data.name || !data.description) {
    throw new Error("Frontmatter must have 'name' and 'description'");
  }

  return { name: data.name, description: data.description };
}

/**
 * Strip frontmatter from SKILL.md content, returning just the body.
 */
export function stripFrontmatter(content: string): string {
  const match = content.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/);
  return match ? content.slice(match[0].length).trim() : content.trim();
}

/**
 * Discover skills from one or more directories.
 * Each skill is a subdirectory containing a SKILL.md file.
 * First skill with a given name wins (allows project-level overrides).
 */
export async function discoverSkills(
  directories: string[],
): Promise<SkillMetadata[]> {
  const skills: SkillMetadata[] = [];
  const seenNames = new Set<string>();

  for (const dir of directories) {
    let entries;
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      continue; // Skip directories that don't exist
    }

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;

      const skillDir = join(dir, entry.name);
      const skillFile = join(skillDir, "SKILL.md");

      try {
        const content = await readFile(skillFile, "utf-8");
        const frontmatter = parseFrontmatter(content);

        // First skill with a given name wins
        if (seenNames.has(frontmatter.name)) continue;
        seenNames.add(frontmatter.name);

        skills.push({
          name: frontmatter.name,
          description: frontmatter.description,
          path: skillDir,
        });
      } catch {
        continue; // Skip skills without valid SKILL.md
      }
    }
  }

  return skills;
}

/**
 * Load the full content of a skill by name (without frontmatter).
 */
export async function loadSkillContent(
  skills: SkillMetadata[],
  name: string,
): Promise<{ content: string; skillDirectory: string } | { error: string }> {
  const skill = skills.find((s) => s.name.toLowerCase() === name.toLowerCase());
  if (!skill) {
    return { error: `Skill '${name}' not found` };
  }

  const skillFile = join(skill.path, "SKILL.md");
  const content = await readFile(skillFile, "utf-8");
  const body = stripFrontmatter(content);

  return { content: body, skillDirectory: skill.path };
}

/**
 * Build a prompt section listing available skills.
 */
export function buildSkillsPrompt(skills: SkillMetadata[]): string {
  if (skills.length === 0) return "";

  const skillsList = skills
    .map((s) => `- **${s.name}**: ${s.description}`)
    .join("\n");

  return [
    "",
    "## Skills",
    "",
    "You have access to specialized skills that provide detailed instructions for specific tasks.",
    "Use the `load_skill` tool to load a skill when the user's request would benefit from specialized instructions.",
    "Load the skill BEFORE starting the task — the skill contains important rules you must follow.",
    "",
    "Available skills:",
    skillsList,
  ].join("\n");
}
