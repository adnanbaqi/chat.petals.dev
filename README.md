Apologies for the misunderstanding! Below is the entire documentation fully formatted in Markdown.

```markdown
# Immutable AI's Swarm-Based Chatbot

A chatbot [web app](https://chat.golab.ai) with HTTP and WebSocket endpoints for large language model (LLM) inference using the [Petals](https://petals.dev) client.

## Interactive Chat

<div align="center">
<img src="https://i.imgur.com/QVTzc6u.png" width="600px">
</div>

You can try out the chatbot at **[chat.golab.ai](https://chat.golab.ai)** or run the backend on your own server using the following commands:

```bash
git clone https://github.com/immutableai/chatbot_petals.git
cd chatbot_petals
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

### 🦄 Deploying with Gunicorn

In production, we recommend using Gunicorn instead of Flask's built-in development server. To deploy with Gunicorn:

```bash
gunicorn app:app --bind 0.0.0.0:5000 --worker-class gthread --threads 100 --timeout 1000
```

The chatbot uses the WebSocket API for communication.

## APIs

The backend exposes two API endpoints:

- [WebSocket API](#websocket-api-apiv2generate) (`/api/v2/generate`, recommended)
- [HTTP API](#http-api-apiv1) (`/api/v1/...`)

It is recommended to use the WebSocket API as it is faster, more efficient, and consumes fewer resources.

## Internal Details

If you are developing your own web app, you can initially use our endpoint at `https://chat.petals.dev/api/...` for research and development. However, for production, we recommend setting up your own backend using the commands above.

> **Note:** We do not recommend using the endpoint at `https://chat.petals.dev/api/...` in production as it has a limited throughput and may be paused or stopped at any time.

### Endpoint System Requirements

<details>
<summary><b>System Requirements</b></summary>

- **CPU-only server**: Ensure you have enough RAM to fit embeddings for all models. If your CPU supports AVX512, the embeddings will be loaded in 16-bit. Otherwise, they will be loaded in 32-bit (which consumes 2x more memory). 
  - AVX512 support is available on modern Intel Xeon CPUs, such as those found in [DigitalOcean](https://digitalocean.com) droplets with dedicated CPUs.
  
- **GPU server**: Ensure you have enough GPU memory to fit the embeddings for all models. The embeddings will be loaded in 16-bit.

- You do not have to serve all models. If memory is limited, you can remove some models in [config.py](config.py).

| Model Family                         | Embeds in 16-bit | Embeds in 32-bit |
|--------------------------------------|------------------|------------------|
| Llama 2 (70B, 70B-Chat), Llama-65B, Guanaco-65B | 1.05 GB | 2.1 GB |
| BLOOM-176B, BLOOMZ-176B | 7.19 GB | 14.38 GB |
</details>

## WebSocket API (`/api/v2/generate`)

This API opens a WebSocket connection to exchange JSON-encoded requests and responses. It can be accessed from any programming language.

<details>
<summary><b>Example code (Javascript)</b></summary>

This example demonstrates opening an inference session with the [stabilityai/StableBeluga2](https://huggingface.co/stabilityai/StableBeluga2) model. It sends the prompt "A cat sat on", and samples new tokens until the total length reaches 30 tokens. Sampling is done with `temperature=0.6` and `top_p=0.9`.

```javascript
const ws = new WebSocket(`wss://chat.petals.dev/api/v2/generate`);
ws.onopen = () => {
    const prompt = "A cat sat on";
    const maxLength = 30;
    ws.send(JSON.stringify({
        type: "open_inference_session", model: "stabilityai/StableBeluga2", max_length: maxLength
    }));
    ws.send(JSON.stringify({
        type: "generate", inputs: prompt, max_length: maxLength, do_sample: 1, temperature: 0.6, top_p: 0.9
    }));
    ws.onmessage = event => {
        const response = JSON.parse(event.data);
        if (response.ok) {
            if (response.outputs === undefined) {
                console.log("Session opened, generating...");
            } else {
                console.log("Generated: " + prompt + response.outputs);
                ws.close();
            }
        } else {
            console.log("Error: " + response.traceback);
            ws.close();
        }
    };
};
```
</details>

🐍 **Using Python on Linux/macOS?** Please consider running the [native Petals client](https://github.com/bigscience-workshop/petals#readme) instead. This way, you can connect to the swarm directly (without this API endpoint) and even run fine-tuning.

The requests must follow this protocol:

### open_inference_session

The first request must be of type **open_inference_session** and include these parameters:

- **model** (str) - Model repository for one of the models defined in [config.py](https://github.com/petals-infra/chat.petals.dev/blob/main/config.py). If you load a model with an adapter, use the adapter repository here instead.
- **max_length** (int) - Max length of generated text (including prefix and intermediate inputs) in tokens.

Notes:

- The inference session created by this request is unique to this WebSocket connection and cannot be reused in other connections.
- The session is closed automatically when the connection is closed (gracefully or abruptly).
- We do not provide API for Falcon-180B due to its [license](https://huggingface.co/spaces/tiiuae/falcon-180b-license/blob/main/LICENSE.txt) restrictions.

Request:

```javascript
{type: "open_inference_session", max_length: 1024}
```

Response:

```javascript
{ok: true}  // If successful
{ok: false, traceback: "..."}  // If failed
```

### generate

The next requests must be of type **generate** and include the same parameters as in the [/api/v1/generate HTTP API](#post-apiv1generate). In contrast to the HTTP API, you can use this API in a streaming fashion, generating a response token-by-token and accepting intermediate prompts from a user (e.g., to make a chatbot).

A new feature of the WebSocket API is the `stop_sequence` parameter (str, optional). If you set it, the server will continue generation with the same parameters unless it generates the `stop_sequence`, so you may get multiple responses without having to send the request again and wait for the round trip's latency.

Intermediate responses contain the field `stop: false`, and the last response contains `stop: true`. For example, you can set `max_new_tokens: 1` and receive tokens one by one as soon as they are generated. Check out the chat's [frontend code](static/chat.js) for a detailed example of how to do that.

Request:

```javascript
{type: "generate", "inputs": "A cat in French is \"", "max_new_tokens": 3}
```

Response (one or multiple):

```javascript
{ok: true, outputs: "chat\".", stop: true}  // If successful
{ok: false, traceback: "..."}  // If failed
```

## HTTP API (`/api/v1/...`)

### POST /api/v1/generate

Parameters:

- **model** (str) - Model repository for one of the models defined in [config.py](https://github.com/petals-infra/chat.petals.dev/blob/main/config.py). If you load a model with an adapter, use the adapter repository here instead.
- **inputs** (str, optional) - New user inputs. May be omitted if you continue generation in an inference session (see below).
- **max_length** (int) - Max length of generated text (including prefix) in tokens.
- **max_new_tokens** (int) - Max number of newly generated tokens (excluding prefix).

Generation parameters (compatible with [.generate()](https://huggingface.co/blog/how-to-generate) from 🤗 Transformers):

- **do_sample** (bool, optional) - If `0` (default), runs [greedy generation](https://huggingface.co/blog/how-to-generate#greedy-search). If `1`, performs [sampling](https://huggingface.co/blog/how-to-generate#sampling) with parameters below.
- **temperature** (float, optional) - Temperature for sampling.
- **top_k** (int, optional) - [Top-k](https://huggingface.co/blog/how-to-generate#top-k-sampling) sampling.
- **top_p** (float, optional) - [Top-p](https://huggingface.co/blog/how-to-generate#top-p-nucleus-sampling) (nucleus) sampling.
- **repetition_penalty** (float, optional) - [Repetition penalty](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation#transformers.GenerationConfig.repetition_penalty), see [paper](https://arxiv.org/abs/1909.05858).

Notes:

- You need to specify either `max_length` or `max_new_tokens`.
- If you'd like to solve downstream tasks in zero-shot mode, start with `do_sample=0` (default).
- If you'd like to make a chatbot or write a long text, start with `do_sample=1, temperature=0.6, top_p=0.9`.
- We do not provide an API for Falcon-180B due to its [license](https://huggingface.co/spaces/tiiuae/falcon-180b-license/blob/main/LICENSE.txt) restrictions.

Returns (JSON):

- **ok** (bool)
- **outputs** (str)
- **traceback** (str) - the Python traceback if `ok == False`

Example (curl):

```bash
$ curl -X POST "https://chat.petals.dev/api/v1/generate" -d "model=meta-llama/Llama-2-70b-chat-hf" -d "inputs=Once upon a time," -d "max_new_tokens=20"
{"ok":true,"outputs":" there was a young woman named Sophia who lived in a small village nestled in the rolling hills"}
```
```
