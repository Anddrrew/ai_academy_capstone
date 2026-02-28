import { createAgentUIStreamResponse, type UIMessage } from "ai";

import { chatRequestSchema } from "./schema";
import { createMainAgent } from "../agents/main";
import { evaluateAssistantResponse } from "../agents/judge";
import { evaluationStorage } from "../services/evaluation-storage";

export const maxDuration = 30;

function extractTextFromMessage(message: UIMessage | undefined): string {
  if (!message?.parts?.length) {
    return "";
  }

  const textParts = message.parts.flatMap((part) => {
    if (part.type !== "text") {
      return [];
    }
    return [typeof part.text === "string" ? part.text : ""];
  });

  return textParts.join("\n").trim();
}

export async function POST(req: Request) {
  console.log("Received chat request");
  const body = chatRequestSchema.safeParse(await req.json());

  if (!body.success) {
    return Response.json(
      {
        error: "Invalid request body",
        details: body.error.flatten(),
      },
      { status: 400 },
    );
  }

  const userId = body.data.userId;
  const messages = body.data.messages as UIMessage[];
  const mainAgent = await createMainAgent(userId);
  const lastUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");

  return createAgentUIStreamResponse({
    agent: mainAgent,
    uiMessages: messages,
    sendReasoning: true,
    sendSources: true,
    onFinish: async ({ responseMessage }) => {
      try {
        const evaluation = await evaluateAssistantResponse({
          userInput: lastUserMessage,
          responseMessage,
        });

        const userQuestion = extractTextFromMessage(lastUserMessage);
        const assistantAnswer = extractTextFromMessage(responseMessage);

        const evaluationId = await evaluationStorage.save({
          userId,
          userQuestion,
          assistantAnswer,
          evaluation,
        });

        console.info("Judge evaluation:", {
          evaluationId,
          userId,
          score: evaluation.score,
        });
      } catch (error) {
        console.error("Judge evaluation failed:", error);
      }
    },
  });
}
