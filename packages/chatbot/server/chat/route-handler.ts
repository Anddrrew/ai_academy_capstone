import { createAgentUIStreamResponse, type UIMessage } from "ai";

import { chatRequestSchema } from "./schema";
import { createMainAgent } from "../agents/main";
import { evaluateAssistantResponse } from "../agents/judge";

export const maxDuration = 30;


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

  console.log(JSON.stringify({ userId, messages }, null, 2));
  const { agent: mainAgent, toolsMeta } = await createMainAgent(userId);
  const lastUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");

  return createAgentUIStreamResponse({
    agent: mainAgent,
    uiMessages: messages,
    sendReasoning: true,
    sendSources: true,
    onFinish: ({ responseMessage }) => {
      evaluateAssistantResponse({
        userId,
        userInput: lastUserMessage,
        responseMessage,
        availableTools: toolsMeta,
      }).catch((error) => {
        console.error("Judge evaluation failed:", error);
      });
    },
  });
}
