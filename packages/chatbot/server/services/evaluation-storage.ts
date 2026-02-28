import { createHash } from "node:crypto";

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
  private collectionEnsured = false;
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
    if (this.collectionEnsured) {
      return;
    }

    const exists = await this.qdrant.collectionExists(this.collectionName);
    if (!exists) {
      await this.qdrant.createCollection(this.collectionName, {
        vectors: {
          size: config.EMBEDDING_VECTOR_SIZE,
          distance: "Cosine",
        },
      });
    }

    this.collectionEnsured = true;
  }

  async save({
    userId,
    userQuestion,
    assistantAnswer,
    evaluation,
  }: SaveEvaluationInput): Promise<string> {
    await this.ensureCollection();

    const createdAt = Math.floor(Date.now() / 1000);
    const fingerprint = `${userId}:${userQuestion}:${assistantAnswer}:${evaluation.score}:${evaluation.feedback}`;
    const id = createHash("sha256")
      .update(fingerprint)
      .digest("hex")
      .slice(0, 16);
    const vector = await embedderService.embedQuery(
      [userQuestion, assistantAnswer, evaluation.feedback].join("\n"),
    );

    await this.qdrant.upsert(this.collectionName, {
      wait: true,
      points: [
        {
          id,
          vector,
          payload: {
            user_id: userId,
            user_question: userQuestion,
            assistant_answer: assistantAnswer,
            score: evaluation.score,
            feedback: evaluation.feedback,
            created_at: createdAt,
          },
        },
      ],
    });

    return id;
  }
}

export const evaluationStorage = EvaluationStorage.getInstance();
