# LM Studio Model Setup

## Requirements

1. Download a model compatible with LM Studio (e.g., Mistral 7B, Llama 2)
2. Place the model files in this directory
3. The model should be in GGUF format

## Recommended Models

For testing purposes, we recommend using one of these models:

1. mistral-7b-instruct-v0.1.Q4_K_M.gguf
   - Size: ~4GB
   - Good balance of performance and resource usage
   - [Download Link](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF)

2. llama-2-7b-chat.Q4_K_M.gguf
   - Size: ~4GB
   - Good for chat-based interactions
   - [Download Link](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)

## Setup Instructions

1. Download your chosen model from Hugging Face or other sources
2. Place the .gguf file in this directory
3. Update the model name in your environment configuration if different from default

## Testing

Once you have placed the model file in this directory, you can run the integration tests:

```bash
./scripts/test_lmstudio.sh
```

This will:
1. Start the LM Studio service with the model
2. Run the integration tests
3. Clean up services when done
