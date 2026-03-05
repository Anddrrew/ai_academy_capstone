import { randomUUID } from "node:crypto";

import { QdrantClient } from "@qdrant/qdrant-js";

import { config, qdrantCollections } from "@/server/config";
import type { EvaluationFeedback } from "@/server/agents/judge";
import { embedderService } from "@/server/services/embedder";

export type EvaluationRecord = {
  id: string;
  userId: string;
  userQuestion: string;
  assistantTrace: string;
  availableTools: string[];
  score: EvaluationFeedback["score"];
  feedback: string;
  criteria: EvaluationFeedback["criteria"];
  issues: EvaluationFeedback["issues"];
  createdAt: number;
};

type SaveEvaluationInput = {
  userId: string;
  userQuestion: string;
  assistantTrace: string;
  availableTools: string[];
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
    assistantTrace,
    availableTools,
    evaluation,
  }: SaveEvaluationInput) {
    await this.ensureCollection();
    const createdAt = Math.floor(Date.now() / 1000);
    const textToEmbed = [userQuestion, assistantTrace, evaluation.feedback]
      .join("\n")
      .slice(0, 4000);
    const vector = await embedderService.embedQuery(textToEmbed);

    await this.qdrant.upsert(this.collectionName, {
      wait: true,
      points: [
        {
          id: randomUUID(),
          vector,
          payload: {
            userId,
            userQuestion,
            assistantTrace,
            availableTools,
            score: evaluation.score,
            feedback: evaluation.feedback,
            criteria: evaluation.criteria,
            issues: evaluation.issues,
            createdAt,
          },
        },
      ],
    });
  }
}

export const evaluationStorage = EvaluationStorage.getInstance();
