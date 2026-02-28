import { createOpenAI } from "@ai-sdk/openai";
import { Output, ToolLoopAgent, stepCountIs, type UIMessage } from "ai";

import { config } from "@/server/config";
import { JUDGE_AGENT_SYSTEM_PROMPT } from "./prompt";
import { evaluationFeedbackSchema, type EvaluationFeedback } from "./schema";

const provider = createOpenAI({
  apiKey: config.OPENAI_API_KEY,
});

const judgeAgent = new ToolLoopAgent({
  model: provider.responses(config.OPENAI_JUDGE_MODEL),
  instructions: JUDGE_AGENT_SYSTEM_PROMPT,
  output: Output.object({
    schema: evaluationFeedbackSchema,
  }),
  stopWhen: stepCountIs(1),
  providerOptions: {
    openai: {
      reasoningEffort: "high",
      reasoningSummary: "auto",
    },
  },
});

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

function extractToolParts(message: UIMessage | undefined) {
  if (!message?.parts?.length) {
    return [];
  }

  return message.parts.filter((part) =>
    part.type.startsWith("tool-"),
  ) as unknown[];
}

export async function evaluateAssistantResponse({
  userInput,
  responseMessage,
}: {
  userInput: UIMessage | undefined;
  responseMessage: UIMessage | undefined;
}): Promise<EvaluationFeedback> {
  const userText = extractTextFromMessage(userInput);
  const assistantText = extractTextFromMessage(responseMessage);
  const toolCalls = extractToolParts(responseMessage);

  const result = await judgeAgent.generate({
    prompt: [
      `User question:\n${userText || "(empty)"}`,
      `Assistant answer:\n${assistantText || "(empty)"}`,
      `Tool call details:\n${JSON.stringify(toolCalls)}`,
    ].join("\n\n"),
  });

  return result.output;
}
