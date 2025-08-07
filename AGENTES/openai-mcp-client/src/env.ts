// TODO: Move to .env file

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY")!;
const MCP_SERVER_COMMAND = Deno.env.get("MCP_SERVER_COMMAND")!;
const MCP_SERVER_ARGS = JSON.parse(Deno.env.get("MCP_SERVER_ARGS") || "[]")!;
const DEBUG = Deno.env.get("DEBUG") === "true";
const OPENAI_MODEL = Deno.env.get("OPENAI_MODEL") || "gpt-4o-mini";

if (!OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY is not set");
}

if (!MCP_SERVER_COMMAND) {
  throw new Error("MCP_SERVER_COMMAND is not set");
}

if (!MCP_SERVER_ARGS) {
  throw new Error("MCP_SERVER_ARGS is not set");
}

export {
  OPENAI_API_KEY,
  MCP_SERVER_COMMAND,
  MCP_SERVER_ARGS,
  DEBUG,
  OPENAI_MODEL,
};
