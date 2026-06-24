# LLM Integration

- Use `${LLM_MODEL}` in agent config YAML files instead of provider-specific model placeholders. (Neutral placeholders reduce config drift when provider wiring changes.)
- Retry with `FALLBACK_MODEL` only after transient LLM execution failures, and re-raise non-transient errors unchanged. (Fallback should preserve availability without masking real logic or configuration bugs.)
