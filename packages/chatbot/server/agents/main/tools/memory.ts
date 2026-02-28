import { memoryStorage } from "@/server/services/memory-storage";
import { tool } from "ai";
import { z } from "zod";

export function createMemoryTools(userId: string) {
  const searchMemoriesTool = tool({
    description:
      "Search user memories for relevant preferences, facts, or prior context.",
    inputSchema: z.object({
      query: z.string(),
    }),
    execute: async ({ query }) => {
      const memories = await memoryStorage.search(userId, query);
      return { memories };
    },
  });

  const saveMemoryTool = tool({
    description:
      "Save a durable user memory when the user shares a preference, fact, or recurring context.",
    inputSchema: z.object({
      content: z.string(),
    }),
    execute: async ({ content }) => {
      const id = await memoryStorage.save(userId, content);
      return { status: "saved", id };
    },
  });

  const listMemoriesTool = tool({
    description: "List all saved memories for the current user.",
    inputSchema: z.object({}),
    execute: async () => {
      const memories = await memoryStorage.list(userId);
      return { memories };
    },
  });

  const deleteMemoryTool = tool({
    description: "Delete an outdated or incorrect user memory by memory id.",
    inputSchema: z.object({
      memory_id: z.string(),
    }),
    execute: async ({ memory_id }) => {
      await memoryStorage.delete(memory_id);
      return { status: "deleted", id: memory_id };
    },
  });

  return {
    search_memories: searchMemoriesTool,
    save_memory: saveMemoryTool,
    list_memories: listMemoriesTool,
    delete_memory: deleteMemoryTool,
  };
}
