# Intro

This is a simple example of how to use the Model Context Protocol (MCP) with OpenAI's API to create a simple agent acting from a chat context. Feel free to use this as a starting point for your own projects.

# Setup Guide

- Ensure Deno v2 is installed
- Run `deno install` to install dependencies
- Copy `.env.example` to `.env` and fill in the values
  - You can choose any MCP server you like - bring your own or use one from the official [MCP server list](https://github.com/modelcontextprotocol/servers/tree/main)
- Run `deno run dev` to start the application

# Warning

_**Chat messages are appended and currently the entire conversation is always sent to the server. This can rack up a lot of tokens and cost a lot of money, depending on the length of the conversation, the model you are using, and the size of the context.**_

# Limitations

This implementation currently only supports tool call responses of type `text`. Other resource can be implemented in `applyToolCallIfExists` in [src/openai-utils.ts](src/openai-utils.ts).

# Notes

You latest messages are saved in `messages.json` for debugging purposes. These messages will be overwritten every time you run the application, so make sure to create a copy of the file before running the application again, if you want to keep the previous messages.

If you want to run the application in debug mode, set the `DEBUG` environment variable to `true` in your `.env` file. This will print out more information about the messages and tool calls.
