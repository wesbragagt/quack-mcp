import { QuackMCPServer } from "./mcp.ts";

export { QuackMCPServer };

if (process.argv[1] === import.meta.url.replace('file://', '')) {
  const server = new QuackMCPServer();
  server.run().catch(console.error);
}
