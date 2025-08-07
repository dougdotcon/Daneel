import OpenAI from "npm:openai@4.76.1";
import { mcpClient } from "./client.ts";
import {
  applyToolCallsIfPresent,
  isDone,
  mapToolListToOpenAiTools,
} from "./openai-utils.ts";
import { OPENAI_API_KEY, OPENAI_MODEL } from "./env.ts";
import { MessageHandler, type MessageType } from "./messages.ts";
import { performNextStepSystemPrompt } from "./prompts.ts";
import { askForInput } from "./cli.ts";

const agentLoop = async (
  openai: OpenAI,
  openAiTools: OpenAI.Chat.Completions.ChatCompletionTool[],
  messagesHandler: MessageHandler
) => {
  // Maximum number of autonomous steps
  const maxIterations = 10;

  for (let i = 0; i < maxIterations; i++) {
    const response = await openai.chat.completions.create({
      model: OPENAI_MODEL,
      temperature: 0.2,
      messages: messagesHandler.getMessages(),
      tools: openAiTools,
    });

    messagesHandler.addMessage(response.choices[0].message);

    if (isDone(response)) {
      break;
    }

    const toolCallResponse = await applyToolCallsIfPresent(response);

    if (toolCallResponse.length) {
      messagesHandler.addMessages(toolCallResponse);
    }

    messagesHandler.addMessage(performNextStepSystemPrompt);
  }
};

const main = async () => {
  const messagesHandler = new MessageHandler();

  const openai = new OpenAI({
    apiKey: OPENAI_API_KEY,
  });

  const mcpToolsList = await mcpClient.listTools();
  const openAiTools = mapToolListToOpenAiTools(mcpToolsList);

  try {
    while (true) {
      const input = await askForInput();

      if (input === "exit") {
        messagesHandler.storeMessages();
        break;
      }

      messagesHandler.addMessage({
        role: "user",
        content: input,
      } as MessageType);

      await agentLoop(openai, openAiTools, messagesHandler);
    }
  } catch (error) {
    console.error(error);
    messagesHandler.storeMessages();
  } finally {
    mcpClient.close();
  }
};

await main();
