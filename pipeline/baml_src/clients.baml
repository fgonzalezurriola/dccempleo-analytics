client<llm> OpenCodeBridge {
  provider openai-generic
  options {
    base_url env.BAML_PROXY_BASE_URL
    api_key env.BAML_PROXY_API_KEY
    model env.BAML_MODEL
  }
}
