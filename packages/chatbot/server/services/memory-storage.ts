import { randomUUID } from "node:crypto";

import { QdrantClient } from "@qdrant/qdrant-js";

import { config, qdrantCollections } from "@/server/config";
import { embedderService } from "@/server/services/embedder";

export type MemoryRecord = {
  id: string;
  text: string;
  createdAt: number;
};

export class MemoryStorage {
  private static instance: MemoryStorage | null = null;
  private readonly qdrant: QdrantClient;
  private readonly collectionName = qdrantCollections.memory;

  private constructor() {
    this.qdrant = new QdrantClient({ url: config.qdrant.url });
  }

  static getInstance(): MemoryStorage {
    if (!MemoryStorage.instance) {
      MemoryStorage.instance = new MemoryStorage();
    }
    return MemoryStorage.instance;
  }

  private async ensureCollection(): Promise<void> {
    const { exists } = await this.qdrant.collectionExists(this.collectionName);
    if (!exists) {
      await this.qdrant.createCollection(this.collectionName, {
        vectors: {
          size: config.embedding.vectorSize,
          distance: "Cosine",
        },
      });
    }
  }

  private userFilter(userId: string) {
    return {
      must: [
        {
          key: "userId",
          match: { value: userId },
        },
      ],
    };
  }

  async save(userId: string, text: string) {
    await this.ensureCollection();
    const vector = await embedderService.embedQuery(text);
    const id = randomUUID();

    await this.qdrant.upsert(this.collectionName, {
      wait: true,
      points: [
        {
          id,
          vector,
          payload: {
            userId,
            createdAt: Math.floor(Date.now() / 1000),
            text,
          },
        },
      ],
    });

    return id;
  }

  async search(
    userId: string,
    query: string,
    k = 5,
  ): Promise<Array<{ id: string; text: string; score: number | null }>> {
    await this.ensureCollection();
    const vector = await embedderService.embedQuery(query);

    const points = await this.qdrant.search(this.collectionName, {
      vector,
      filter: this.userFilter(userId),
      limit: k,
      with_payload: true,
    });

    return points.map((point) => ({
      id: String(point.id),
      text: String(point.payload?.text ?? ""),
      score: point.score ?? null,
    }));
  }

  async list(userId: string): Promise<MemoryRecord[]> {
    await this.ensureCollection();

    const data = await this.qdrant.scroll(this.collectionName, {
      filter: this.userFilter(userId),
      order_by: {
        key: "createdAt",
        direction: "desc",
      },
      with_payload: true,
      limit: 100,
    });

    return data.points.map((point) => ({
      id: String(point.id),
      text: String(point.payload?.text ?? ""),
      createdAt: Number(point.payload?.createdAt ?? 0),
    }));
  }

  async delete(memoryId: string): Promise<void> {
    await this.ensureCollection();
    await this.qdrant.delete(this.collectionName, {
      wait: true,
      points: [memoryId],
    });
  }
}

export const memoryStorage = MemoryStorage.getInstance();
