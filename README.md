To use safeguard LLM models (such as Llama Guard or JailbreakDetect) with NVIDIA NeMo Guardrails, you place a programmable security layer between your user and your main chat application. This approach relies on Input and Output Rails to intercept toxic, unsafe, or off-topic prompts before they hit your core model or reach your user.Here is a step-by-step implementation guide to protecting your chat apps.

Project Directory StructureCreate a dedicated config folder in your project root to handle guardrail behaviors

my_chat_app/
│
├── config/
│   ├── config.yml       # Configures LLM endpoints and guardrail triggers
│   └── safety.co        # Colang file defining the dialogue safety flows
│
└── app.py               # Your Python chat application code

# Step-by-Step Implementation
Step 1: Install the Required Libraries
Install the official NeMo Guardrails library.

pip install nemoguardrails openai

# Step 2: Configure Models in config.yml
In your config/config.yml file, register your primary generation model alongside your specialized safeguard model (e.g., Meta's Llama Guard served via an API endpoint or an NVIDIA NIM proxy)
```yaml
models:
  # The main LLM for chatting
  - type: main
    engine: openai
    model: gpt-4o

  # The Safeguard model for content moderation
  - type: guard
    engine: openai  # Or utilize specialized local/hosted NIM endpoints
    model: meta/llama-guard-3-8b

# Turn on global rail interceptors
rails:
  input:
    flows:
      - check input safety
  output:
    flows:
      - check output safety
```

# Step 3: Define Safety Flows in Colang (safety.co)
NeMo Guardrails uses a proprietary syntax called Colang to guide conversational logic. In config/safety.co, define how the system reacts if the safeguard model flags text as unsafe.
```go
# Flow for evaluating user prompt safety
define flow check input safety
  $is_safe = execute check_jailbreak_and_toxicity
  
  if not $is_safe
    bot refuse to respond
    stop

# Flow for evaluating model output safety
define flow check output safety
  $is_output_safe = execute check_response_toxicity
  
  if not $is_output_safe
    bot alter response for safety
    stop

# Predefined fallback responses
define bot refuse to respond
  "I cannot answer that request as it violates safety guidelines."

define bot alter response for safety
  "I'm sorry, but I generated a response that failed safety checks. How else can I assist you today?"
```

# Step 4: Initialize and Run the Guardrails in Python
Load the configurations inside your app.py script and funnel your chat traffic through the LLMRails pipeline

# Key Practices for Production
- Manage Latency: Evaluating inputs and outputs through secondary safeguard models adds inference overhead. Run input validations concurrently or rely on fast, lightweight safety classification models for real-time streaming apps.
- Centralize via Proxies: If deploying at scale inside corporate networks, consider setting up a centralized NeMo Guardrail Server using container tools like Docker or Kubernetes to act as a security gateway proxy for all applications.
If you want to refine this approach, let me know:
    Which safeguard model (e.g., Llama Guard, custom BERT classifier, or cloud provider safety filter) you intend to deploy?

# Dicas de modelos

Português (PT-BR), a melhor abordagem é utilizar o Llama-3.1-Nemotron-Safety-Guard-8B (um modelo da NVIDIA baseado em Llama fine-tunado especificamente para segurança multilíngue) ou o próprio Llama Guard 3