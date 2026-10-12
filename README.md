To deploy NVIDIA NeMo Guardrails as a drop-in security proxy, you run the NeMo Guardrails API Server. This server exposes an OpenAI-compliant HTTP API (specifically the /v1/chat/completions endpoint).Instead of routing traffic from your existing chat application directly to your vLLM or OpenAI instance, you point your chat app’s base_url to the NeMo Guardrails server. The proxy intercepts the request, runs your input rails, calls the downstream backend LLM, runs your output rails, and streams the compliant response back to your client seamlessly.Here is how the proxy architecture functions and how to deploy it on a enterprise Red Hat OpenShift Kubernetes Cluster using native OpenShift GitOps tools.


# How the Proxy Mechanism Works

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



## Step 1: Wrap Your Guardrail Config into an OpenShift ConfigMap
On Red Hat OpenShift, you inject your custom config.yml and safety.co files into the container using a native Kubernetes ConfigMap.Create a file named nemo-configmap.yaml


## Step 2: Choose Your OpenShift Deployment Strategy
There are two primary ways to run the server on OpenShift:Option A: Red Hat OpenShift AI (Recommended Enterprise Path)If you have Red Hat OpenShift AI (RHOAI) installed, NeMo Guardrails is integrated natively through the TrustyAI Operator. You simply declare a NemoGuardrails Custom Resource (CR) pointing to your ConfigMap, and OpenShift scales the proxy for you automatically.Create nemo-cr.yaml

### Option B: Standard Kubernetes Deployment (Pure Python Server)
If you are running vanilla OpenShift without the RHOAI operator, you can build a standard deployment utilizing the official open-source NeMo Guardrails container image, which triggers the Python nemoguardrails server runtime command natively.Create nemo-deployment.yaml

## Step 3: Swapping the base_url in your Chat App
Get your deployment's public endpoint using OpenShift CLI
oc get route nemo-guardrails-api -n MEU-NAMESPACE-AI

in your existing Python chat interface codebase (whether it uses LangChain, LlamaIndex, or raw OpenAI clients), replace your old LLM connection endpoint with this proxy address:

```python
import openai

# Drop-in replacement targeting your NeMo proxy on OpenShift
client = openai.OpenAI(
    base_url="https://your-cluster.com",
    api_key="your-existing-key-or-any-string"
)

# Your legacy application logic remains completely identical!
response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct", # Matches configuration block
    messages=[
        {"role": "user", "content": "Como emitir a segunda via do boleto?"}
    ]
)

print(response.choices[0].message.content)
```

If a user tries to break the rules (e.g., asking for a recipe), the NeMo proxy server intercepts the request before it routes over the network to your core backend vLLM cluster, instantly outputting your pre-coded Portuguese off-topic message back to the chat application client seamlessly.


# Apply it to your cluster:
oc apply -f nemo-configmap.yaml

Apply it via oc apply -f nemo-cr.yaml.
OpenShift will spin up the server and create a cluster Route for you

Apply it: oc apply -f nemo-deployment.yaml.

