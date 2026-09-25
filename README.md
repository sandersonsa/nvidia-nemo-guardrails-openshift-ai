To use safeguard LLM models (such as Llama Guard or JailbreakDetect) with NVIDIA NeMo Guardrails, you place a programmable security layer between your user and your main chat application. This approach relies on Input and Output Rails to intercept toxic, unsafe, or off-topic prompts before they hit your core model or reach your user.Here is a step-by-step implementation guide to protecting your chat apps.

Project Directory StructureCreate a dedicated config folder in your project root to handle guardrail behaviors

meu_app_seguro/
│
├── config/
│   ├── config.yml       # Endpoints locais + ativação de PII e Off-topic
│   └── safety.co        # Fluxos em PT-BR para PII, Off-topic e Segurança
│
├── requirements.txt     # Dependências do projeto
└── app.py               # Código principal que executa o Chat


# Step-by-Step Implementation
Step 1: Install the Required Libraries
Install the official NeMo Guardrails library.

pip install nemoguardrails openai

# Step 2: Configure Models in config.yml
Neste arquivo, você apontará o NeMo Guardrails para as portas onde seus modelos locais estão rodando (por padrão, o vLLM ou Ollama costumam usar a porta 8000 ou 11434)
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
O arquivo Colang dita o comportamento do chat. Como o público-alvo fala português, programamos as mensagens de recusa diretamente em PT-BR

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


# Executar
## Passo 1: Instalar as dependências
Abra o terminal na pasta do projeto e instale os pacotes:
pip install -r requirements.txt

## Passo 2: Inicializar o vLLM para o Modelo Principal
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.45

## Passo 3: Inicializar o vLLM para o Modelo de Segurança
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-Guard-3-8B \
    --port 8001 \
    --gpu-memory-utilization 0.45

## Passo 4: Criar e Executar o Script do Aplicativo (app.py)
python app-test.py


<!-- Abra um terminal e inicie o servidor do seu modelo principal (Llama-3.1-8B-Instruct) na porta 8000:
vllm-openai --model meta-llama/Llama-3.1-8B-Instruct --served-model-name meta-llama/Llama-3.1-8B-Instruct

## Passo 3: Inicializar o vLLM para o Modelo de Segurança (Guard)
Abra um SEGUNDO terminal e inicie o modelo de segurança (Llama Guard) na porta 8001:
vllm-openai --model meta-llama/Llama-Guard-3-8B --served-model-name meta-llama/Llama-Guard-3-8B

## Passo 4: Executar a Aplicação Python com NeMo Guardrails
Com os dois servidores rodando, execute o script Python:
python app.py

Se for usar a versão estendida (PII e Off-topic), use o arquivo de configuração correspondente:
config: config-extendido.yml
safety: safety-extendido.co
 -->
