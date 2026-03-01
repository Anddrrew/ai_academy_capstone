import { createHash, randomUUID } from "node:crypto";

import { QdrantClient } from "@qdrant/qdrant-js";

import { config, qdrantCollections } from "@/server/config";
import type { EvaluationFeedback } from "@/server/agents/judge";
import { embedderService } from "@/server/services/embedder";

export type EvaluationRecord = {
  id: string;
  userId: string;
  userQuestion: string;
  assistantAnswer: string;
  score: EvaluationFeedback["score"];
  feedback: string;
  createdAt: number;
};

type SaveEvaluationInput = {
  userId: string;
  userQuestion: string;
  assistantAnswer: string;
  evaluation: EvaluationFeedback;
};

export class EvaluationStorage {
  private static instance: EvaluationStorage | null = null;
  private readonly qdrant: QdrantClient;
  private readonly collectionName = qdrantCollections.evaluation;

  private constructor() {
    this.qdrant = new QdrantClient({ url: config.QDRANT_URL });
  }

  static getInstance(): EvaluationStorage {
    if (!EvaluationStorage.instance) {
      EvaluationStorage.instance = new EvaluationStorage();
    }
    return EvaluationStorage.instance;
  }

  private async ensureCollection(): Promise<void> {
    const { exists } = await this.qdrant.collectionExists(this.collectionName);
    if (!exists) {
      await this.qdrant.createCollection(this.collectionName, {
        vectors: {
          size: config.EMBEDDING_VECTOR_SIZE,
          distance: "Cosine",
        },
      });
    }
  }

  async save({
    userId,
    userQuestion,
    assistantAnswer,
    evaluation,
  }: SaveEvaluationInput) {
    await this.ensureCollection();
    const createdAt = Math.floor(Date.now() / 1000);
    const vector = await embedderService.embedQuery(
      [userQuestion, assistantAnswer, evaluation.feedback].join("\n"),
    );

    await this.qdrant.upsert(this.collectionName, {
      wait: true,
      points: [
        {
          id: randomUUID(),
          vector,
          payload: {
            userId,
            userQuestion,
            assistantAnswer,
            score: evaluation.score,
            feedback: evaluation.feedback,
            createdAt,
          },
        },
      ],
    });
  }
}

export const evaluationStorage = EvaluationStorage.getInstance();
