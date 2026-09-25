To enforce a strict allowed-list of topics using NeMo Guardrails, you can use Topical Rails. Instead of relying on a prompt classification model, NeMo Guardrails maps user inputs to specific semantic intents using text embeddings. If the user's intent does not match the allowed definitions, it triggers a fallback flow.Here is the updated configuration to enforce a strict policy exclusively for "Faturamento" (Billing) and "Modem de Internet" (Internet Modem).

Project Directory StructureCreate a dedicated config folder in your project root to handle guardrail behaviors

meu_app_seguro/
│
├── config/
│   ├── config.yml       # Endpoints locais + ativação de PII e Off-topic
│   └── safety.co        # Fluxos em PT-BR para PII, Off-topic e Segurança
│
├── requirements.txt     # Dependências do projeto
└── app.py               # Código principal que executa o Chat


How this behaves:When you type "Como faço para emitir a segunda via do meu boleto?", NeMo computes embeddings, finds it highly similar to user perguntar sobre faturamento, and executes tratar faturamento.When you type "Quais são os planos de TV a cabo de vocês?", it checks against both definitions. Since "TV a cabo" falls below the similarity threshold for Billing and Modems, it defaults to the tratar fora do topico user wildcard (user ...), returning your customized Portuguese restriction notice.