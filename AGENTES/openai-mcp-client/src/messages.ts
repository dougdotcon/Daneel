import OpenAI from "npm:openai@4.76.1";
import { printMessage } from "./cli.ts";
import fs from "node:fs";
import {
  initialMessageSystemPrompt,
  performNextStepSystemPrompt,
} from "./prompts.ts";
import { DEBUG } from "./env.ts";

export type MessageType =
  | OpenAI.Chat.Completions.ChatCompletionMessageParam
  | OpenAI.Chat.Completions.ChatCompletionMessage;

class MessageHandler {
  private messages: MessageType[] = [initialMessageSystemPrompt];
  private debug: boolean;

  constructor() {
    this.debug = DEBUG;
  }

  public loadMessages(
    addPerformNextStep: boolean = true
  ): MessageType[] | null {
    try {
      const rawMessages = fs.readFileSync("messages.json", "utf8");
      const messages = JSON.parse(rawMessages);

      if (addPerformNextStep) {
        messages.push(performNextStepSystemPrompt);
      }

      return messages;
    } catch (e) {
      console.log("Error loading messages", e);
      return null;
    }
  }

  public addMessage(message: MessageType) {
    this.messages.push(message);
    printMessage(message, this.debug);
  }

  public addMessages(messages: MessageType[]) {
    messages.forEach((message) => this.addMessage(message));
  }

  public storeMessages() {
    fs.writeFileSync("messages.json", JSON.stringify(this.messages, null, 2));
  }

  public getMessages() {
    return this.messages;
  }
}

export { MessageHandler };
