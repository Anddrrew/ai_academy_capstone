import { createOpenAI } from "@ai-sdk/openai";
import { Output, ToolLoopAgent, stepCountIs, type UIMessage } from "ai";

import { config } from "@/server/config";
import { evaluationStorage } from "@/server/services/evaluation-storage";
import { JUDGE_AGENT_SYSTEM_PROMPT } from "./prompt";
import { evaluationFeedbackSchema } from "./schema";

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

type AnyPart = { type: string; [key: string]: unknown };

function extractText(message: UIMessage | undefined): string {
  if (!message?.parts?.length) return "";
  return (message.parts as AnyPart[])
    .filter((p) => p.type === "text")
    .map((p) => String(p.text ?? ""))
    .join("\n")
    .trim();
}

function extractOrderedTrace(message: UIMessage | undefined): string {
  if (!message?.parts?.length) return "(empty)";

  const blocks: string[] = [];
  let toolIndex = 0;

  for (const part of message.parts) {
    if (part.type === "reasoning" && part.text) {
      blocks.push(`reasoning:\n${String(part.text).trim()}`);
    } else if (
      (part.type.startsWith("tool-") || part.type === "dynamic-tool") &&
      part.state === "output-available"
    ) {
      toolIndex++;
      const name =
        part.type === "dynamic-tool"
          ? String(part.toolName ?? "unknown")
          : part.type.slice("tool-".length);
      const inputJson = JSON.stringify(part.input, null, 2).slice(0, 2000);
      const outputJson = JSON.stringify(part.output, null, 2).slice(0, 2000);
      blocks.push(
        [
          `tool call [${toolIndex}]: ${name}`,
          `input:\n${inputJson}`,
          `output:\n${outputJson}`,
        ].join("\n"),
      );
    } else if (part.type === "text" && part.text) {
      blocks.push(`final message:\n${String(part.text).trim()}`);
    }
  }

  return blocks.join("\n\n") || "(empty)";
}

export async function evaluateAssistantResponse({
  userId,
  userInput,
  responseMessage,
  availableTools,
}: {
  userId: string;
  userInput: UIMessage | undefined;
  responseMessage: UIMessage | undefined;
  availableTools: { name: string; description: string }[];
}): Promise<void> {
  const userText = extractText(userInput);
  const trace = extractOrderedTrace(responseMessage);
  const availableToolsText = availableTools
    .map((t) => `- ${t.name}: ${t.description}`)
    .join("\n");

  const sections: string[] = [
    `## User Question\n${userText || "(empty)"}`,
    `## Assistant Response\n${trace}`,
    `## Tools Available to Assistant\n${availableToolsText || "(none)"}`,
  ];

  console.log(sections.join("\n\n"));
  const result = await judgeAgent.generate({
    prompt: sections.join("\n\n"),
  });

  await evaluationStorage.save({
    userId,
    userQuestion: userText,
    assistantTrace: trace,
    availableTools: availableTools.map((t) => t.name),
    evaluation: result.output,
  });
}
