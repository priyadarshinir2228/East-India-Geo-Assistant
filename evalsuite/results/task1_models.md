## Task 1: models

| Component | Model | Context / size | Speed | Memory | Output |
|---|---|---|---|---|---|
| LLM | models\Qwen2.5-3B-Instruct-Q4_K_M.gguf | n_ctx=8192 | 2.8 tok/s | see llama-server log / Task Manager | text + logprobs=True |
| embedder | BAAI/bge-small-en-v1.5 | dims=384 | 169 texts/s | +484 MB | unit vector, norm=1.00 |
| embedder | intfloat/e5-base-v2 | dims=768 | 35 texts/s | +352 MB | unit vector, norm=1.00 |
| reranker | BAAI/bge-reranker-base | max_length=512 | - | +574 MB | raw logit per pair, e.g. 8.80 vs -10.19 |

LLM parameter count and quantisation come from the GGUF file name and the llama-server start-up log.

```json
{
 "model_path": "models\\Qwen2.5-3B-Instruct-Q4_K_M.gguf",
 "total_slots": 4,
 "build_info": "b11622-77390baa1"
}
```
