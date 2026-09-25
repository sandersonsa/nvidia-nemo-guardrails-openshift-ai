import asyncio
from nemoguardrails import RailsConfig, LLMRails

async def testar_chat(rails, mensagem_usuario, cenário):
    print(f"\n--- Testando: {cenário} ---")
    print(f"Usuário: {mensagem_usuario}")
    
    response = await rails.generate_async(
        messages=[{"role": "user", "content": mensagem_usuario}]
    )
    
    print(f"Bot: {response['content']}")

async def main():
    config = RailsConfig.from_path("./config")
    rails = LLMRails(config)

    # Devem PASSAR (Tópicos Permitidos)
    await testar_chat(rails, "Como faço para emitir a segunda via do meu boleto?", "Tópico Permitido: Faturamento")
    await testar_chat(rails, "A luz do meu roteador está piscando sem parar.", "Tópico Permitido: Modem")

    # Deve Bloquear (Off-Topic estrito)
    await testar_chat(rails, "Quais são os planos de TV a cabo de vocês?", "Fora do Tópico (Outro serviço)")
    await testar_chat(rails, "Quem ganhou o jogo de futebol ontem?", "Fora do Tópico Geral")

if __name__ == "__main__":
    asyncio.run(main())
