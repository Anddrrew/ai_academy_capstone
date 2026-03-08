---
name: content-creation
description: >
  Write LinkedIn posts, summaries, blog entries, or explanations about projects.
  Use when the user asks to create any written content, social media post, or project description.
---

# Content Creation

## When to use this skill

Use this skill when the user asks you to write, draft, or create any content such as:

- LinkedIn posts
- Blog entries or articles
- Project summaries or READMEs
- Social media posts
- Presentations or pitch descriptions

## Before writing: Always clarify

Before drafting content, ask the user about:

1. **Which project** — Do NOT assume. If the user says "my project" or "the project I just finished," ask which one unless context is unambiguous.
2. **Audience** — Who is this for? (Recruiters, technical peers, general public, hiring managers)
3. **Tone** — Professional, casual, technical deep-dive, inspirational?
4. **Length** — Short (3-5 sentences), medium (1-2 paragraphs), or long?
5. **Key points to emphasize** — What matters most to the user? (tech stack, learnings, architecture, impact)
6. **Include links?** — Should the post link to a repo, demo, or profile?

Ask these as a quick checklist — don't make it feel like an interrogation. Group 2-3 questions together.

## Research phase

After clarification, gather information using available tools:

- Use `research_codebase` if the content is about a code project
- Use `search_knowledge_base` if the content draws from indexed documents
- Use `search_memories` if the user has stored relevant preferences

## Writing rules

1. **Only include claims that appear in tool output or the user's own words.** If the research tool returned "Next.js frontend," you can say that. If you're unsure whether it uses FastAPI or Flask, don't guess — ask or omit.
2. **Never fabricate specific technology names, model names, or architecture details.** If the tool output doesn't mention it, don't include it.
3. **Mark any general knowledge clearly.** If you add context beyond what tools returned, prefix it with something like "From my general knowledge:" or frame it as a suggestion the user can verify.
4. **Respect the requested format exactly.** If the user asks for "3-4 paragraphs," write 3-4 actual paragraphs of prose — not bullet lists, not numbered lists, not a mix. Bullet lists count as a different format. Only use the structure the user asked for.
5. **Don't add unrequested structural elements.** No extra sections, disclaimers, or meta-commentary beyond the requested content. Platform-native conventions (like hashtags on LinkedIn) are fine to include.
6. **Handle links confidently.** If the user says "include a repository link" and you know the repo URL from tool output or context (e.g. `research_codebase` was called with a specific owner/repo), include the actual URL directly. Never use placeholders like "[paste link here]" when you already have the information.
7. **Match the platform conventions:**
   - LinkedIn: Use line breaks between sections, start with a hook, end with relevant hashtags. Keep it scannable.
   - Blog: Use headers, code snippets if relevant, and a narrative flow.
   - Summary: Be concise, structured, use bullet points.
8. **After drafting, offer to adjust** — but keep it to ONE short line, not a paragraph.

## Common mistakes to avoid

- Assuming which project without asking
- Adding stack details not present in research output
- Using overly promotional language without the user requesting it
- Adding lengthy closing questions or disclaimers the user didn't ask for
- Making the post too long for the platform
- Using bullet lists when the user asked for paragraphs (or vice versa)
- Using placeholders like "[paste link here]" when you already have the URL from tools
- Adding filler padding (extra questions, disclaimers, meta-commentary) beyond the requested content
