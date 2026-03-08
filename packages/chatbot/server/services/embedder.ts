import { config } from "@/server/config";
import { z } from "zod";

const embedResponseSchema = z.object({
  embeddings: z.array(z.array(z.number())),
});

export class EmbedderService {
  private static instance: EmbedderService | null = null;

  private constructor() {}

  static getInstance(): EmbedderService {
    if (!EmbedderService.instance) {
      EmbedderService.instance = new EmbedderService();
    }
    return EmbedderService.instance;
  }

  async embedQuery(text: string): Promise<number[]> {
    const response = await fetch(config.embedding.publicUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ inputs: [text] }),
    });

    if (!response.ok) {
      const details = await response.text();
      throw new Error(
        `Embedder request failed (${response.status}): ${details}`,
      );
    }

    const data = embedResponseSchema.parse(await response.json());
    const vector = data.embeddings?.[0];
    if (!vector) {
      throw new Error("Embedder response missing vector");
    }
    return vector;
  }
}

export const embedderService = EmbedderService.getInstance();
