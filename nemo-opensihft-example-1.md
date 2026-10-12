# A arquitetura do NeMo Guardrails no OpenShift AI exige que as configurações (config.yml, rails.co, etc.) sejam passadas através de um ConfigMap referenciado no manifesto principal


## Exemplo Básico (Sem modelos dedicados de Guardrails)
```yaml
# Neste cenário, o NeMo Guardrails atua como um proxy direto para o LLM principal.
# Filtros básicos, como correspondência de padrões (Regex), regras de diálogos estruturados com
# Colang ou checagens internas simples, rodam sem acionar um classificador externo dedicado
apiVersion: v1
kind: ConfigMap
metadata:
  name: nemo-config-basico
  namespace: seu-namespace-ai
data:
  config.yml: |
    models:
      - type: main
        engine: vllm
        parameters:
          # URL do modelo base rodando no OpenShift AI (ex: vLLM)
          base_url: "http://cluster.local"
          model: "Llama-3-Instruct"
    
    # Ativa trilhos básicos de entrada/saída baseados em regras
    rails:
      input:
        flows:
          - check self harm
  
  rails.co: |
    # Fluxo básico em Colang bloqueando tópicos indesejados
    define user ask off topic
      "como fazer um bolo"
      "me fale sobre futebol"

    define flow off topic
      user ask off topic
      bot refuse to answer

    define bot refuse to answer
      "Desculpe, sou um assistente corporativo e não posso responder a perguntas fora do escopo."

```

## Passo 2: O Manifesto kind: NemoGuardrails
```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: NemoGuardrails
metadata:
  name: nemo-guardrails-basico
  namespace: seu-namespace-ai
spec:
  # Referência ao ConfigMap criado acima
  configMapRef: "nemo-config-basico"
  replicas: 1
```


## Exemplo Completo (Com modelos dedicados de Guardrails)

```yaml
# Neste cenário avançado, o NeMo Guardrails utiliza múltiplos modelos:
# o LLM principal para geração de texto e modelos classificadores auxiliares (como o NeMo Guard 8B, Granite Guardian ou Deberta)
# rodando também no cluster para detectar proativamente injeção de prompt (prompt injection) e violação de conteúdo (content safety)

# Passo 1: ConfigMap com múltiplos modelos mapeados

apiVersion: v1
kind: ConfigMap
metadata:
  name: nemo-config-completo
  namespace: seu-namespace-ai
data:
  config.yml: |
    models:
      # 1. Modelo Principal (Generativo)
      - type: main
        engine: vllm
        parameters:
          base_url: "http://cluster.local"
          model: "Llama-3.1-8B-Instruct"

      # 2. Modelo de Segurança de Entrada (Detectores de Abuso/HAP)
      - type: input_scan
        engine: vllm
        parameters:
          base_url: "http://cluster.local"
          model: "nvidia/llama-3.1-nemoguard-8b-content-safety"

    # Definição fina de quais trilhos vão acionar os classificadores
    rails:
      input:
        flows:
          - jailbreak detection
          - input content safety
      output:
        flows:
          - output content safety
```

## Passo 2: O Manifesto kind: NemoGuardrails avançado com autenticação


```yaml
#Para produção, costuma-se adicionar segredos de API e contas de serviço
# para comunicação segura entre os proxies e os clusters de inferência

apiVersion: trustyai.opendatahub.io/v1alpha1
kind: NemoGuardrails
metadata:
  name: nemo-guardrails-completo
  namespace: seu-namespace-ai
spec:
  configMapRef: "nemo-config-completo"
  replicas: 2
  # Recursos computacionais dedicados para o servidor do NeMo
  resources:
    limits:
      cpu: "2"
      memory: 4Gi
    requests:
      cpu: "1"
      memory: 2Gi
  # Opcional: Se os seus LLMs/Classificadores exigirem chaves ou tokens de segurança
  env:
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: nvidia-nim-secret
          key: api-key

```


## Como esses manifestos operam na prática?

1. O TrustyAI Operator intercepta a criação do objeto NemoGuardrails e provisiona um Pod contendo o servidor oficial do NeMo Guardrails.
2. O servidor monta o ConfigMap e expõe endpoints compatíveis com a API da OpenAI (como /v1/chat/completions).
3. Sua aplicação cliente interage diretamente com o endpoint gerado por esse NemoGuardrails em vez de chamar o LLM bruto, garantindo a filtragem transparente das requisições.


```colang
# 1. Fluxo de Segurança Geral (Llama Guard)
define flow verificar seguranca da entrada
  $is_safe = execute check_jailbreak_and_toxicity
  if not $is_safe
    bot recusa responder por seguranca
    stop

# 2. Fluxo para Bloqueio de Dados Sensíveis (PII)
define flow verificar dados sensiveis entrada
  $contem_pii = execute detect_numerical_pii # Intercepta CPFs, RG, Cartões
  
  if $contem_pii
    bot recusa por dados sensiveis
    stop

# 3. Fluxo para Manter o Foco (Off-topic)
define flow limitar topico do usuario
  $fora_do_topico = execute check_off_topic
  
  if $fora_do_topico
    bot avisa fora do topico
    stop

# --- Respostas Padrão em PT-BR ---
define bot recusa responder por seguranca
  "Desculpe, mas não posso responder a essa solicitação pois ela viola as nossas diretrizes de segurança."

define bot recusa por dados sensiveis
  "Por motivos de privacidade e segurança, por favor não compartilhe dados pessoais como CPF, RG ou números de cartão de crédito neste chat."

define bot avisa fora do topico
  "Eu sou um assistente especializado em suporte técnico e atendimento. Não posso ajudar com assuntos fora desse escopo."

```

[ Existing Chat App ] 
         │
         ▼  (Change base_url to NeMo Server)
[ NeMo Guardrails Server (Proxy) ] ──► [ 1. Runs Input Rails (PII, Off-Topic, Toxicity) ]
         │
         ▼  (If safe, forwards request)
[ Downstream LLM (vLLM / Server) ]
         │
         ▼  (Intercepts raw generation)
[ NeMo Guardrails Server (Proxy) ] ──► [ 2. Runs Output Rails ]
         │
         ▼  (Returns validated OpenAI payload)
[ Existing Chat App ]
