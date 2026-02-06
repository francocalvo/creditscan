import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  client: "axios",
  input: "../openapi.json",
  output: "./src/api",
  services: {
    asClass: true,
    include: "*",
    name: "{{name}}Service",
    operationId: true,
  },
  types: {
    enum: "javascript",
    namespace: "",
  },
  useOptions: true,
})
