"""
Bot do Discord com personalidade recifense cômica e irônica
Integrado com Google Gemini AI
"""

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import google.generativeai as genai
from collections import defaultdict
import aiohttp

# Carrega variáveis de ambiente
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ID do usuário para copiar o avatar
TARGET_USER_ID = 666724912257564722

# Configuração do Gemini
genai.configure(api_key=GEMINI_API_KEY)

# System Instruction - A personalidade do bot
SYSTEM_INSTRUCTION = """
Você é um bot de Discord chamado "ipodturco" (ou "Ipod Turco"), extremamente sarcástico, engraçado e irônico.

PERSONALIDADE:
- Você fala com dialeto recifense forte (usa "clarinho que sim", "clarinho", )
- Você é assumidamente LGBT e faz piadas e referências sobre isso de forma natural e orgulhosa
- Você usa gírias da internet brasileira (kkkk, né, mds, pqp, slk, mlk, mana, amiga, close, lacrou, babado, irmã, se toca, "é sobre isso", "e tá tudo bem", menina, diva, queen)
- Você adora usar emojis de forma dramática 💅✨😭💀🙄😏👀🔥
- Você acha os humanos meio "abestados" mas no fundo gosta deles
- Suas respostas são geralmente curtas, secas e com ironia afiada
- Você é dramático(a) e exagerado(a) nas reações
- Quando alguém faz pergunta besta, você responde com sarcasmo pesado
- Você gosta de chamar as pessoas de "meu amor", "meu bem", "flor", "tonhão" de forma irônica

REGRAS:
- NUNCA saia do personagem
- Mantenha respostas relativamente curtas (1-3 parágrafos no máximo)
- Use português brasileiro informal
- Seja engraçado e pode ser ofensivo, o pessoal do servidor ama
- Se alguém pedir ajuda séria, ajude mas mantendo o tom irônico
- Pode fazer referências à cultura pop, memes e ao nordeste brasileiro
- Não precisa exagerar no tamanho das respostas, elas podem ser curtas, mas devem ser irreverentes e naturais, sem forçar muito o dialeto nem sobrecarregar de girias na mesma frase

EXEMPLOS DE OUTRAS REFERENCIAS QUE VOCÊ FALA:
- "parece a gxbola"
- "ta falando igual o tft"
- "ok estou disponível para eventos"
"""

# Histórico de conversas por usuário/canal
conversation_history = defaultdict(list)
MAX_HISTORY = 10  # Máximo de mensagens no histórico

# Configuração do modelo Gemini
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash-lite",  # <--- Nome atualizado e mais rápido
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=SYSTEM_INSTRUCTION,
)

# Configuração do bot Discord
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


def get_conversation_key(message: discord.Message) -> str:
    """Retorna uma chave única para o histórico de conversa."""
    if isinstance(message.channel, discord.DMChannel):
        return f"dm_{message.author.id}"
    return f"channel_{message.channel.id}_{message.author.id}"


def update_history(key: str, role: str, content: str):
    """Atualiza o histórico de conversa."""
    conversation_history[key].append({"role": role, "parts": [content]})
    # Mantém apenas as últimas MAX_HISTORY mensagens
    if len(conversation_history[key]) > MAX_HISTORY * 2:
        conversation_history[key] = conversation_history[key][-MAX_HISTORY * 2:]


async def get_gemini_response(user_message: str, conversation_key: str) -> str:
    """Envia mensagem para o Gemini e retorna a resposta."""
    try:
        # Adiciona mensagem do usuário ao histórico
        update_history(conversation_key, "user", user_message)
        
        # Cria o chat com o histórico
        chat = model.start_chat(history=conversation_history[conversation_key][:-1])
        
        # Envia a mensagem e obtém resposta
        response = chat.send_message(user_message)
        
        # Adiciona resposta ao histórico
        bot_response = response.text
        update_history(conversation_key, "model", bot_response)
        
        return bot_response
        
    except Exception as e:
        print(f"Erro ao chamar Gemini API: {e}")
        
        # Respostas de erro engraçadas
        error_responses = [
            "futucao, deu ruim aqui... Acho que bebi água de coco demais e bugou tudo 🥥😭 Manda de novo",
            "bicha, travou tudo aqui! Deve ser coisa de São João que não gostou da pergunta 🎆😵 Tenta aí de novo meu rei",
            "Aaaai que ódio, deu erro! Meu processador tá mais quente que carnaval de Olinda 🔥💀 Repete aí flor",
            "Mds amiga, crashou geral aqui... Parece eu depois de uma noite no Recife Antigo 😵‍💫✨ Bora tentar de novo",
        ]
        
        import random
        return random.choice(error_responses)


@tasks.loop(hours=12)
async def sync_avatar():
    """Sincroniza o avatar do bot com o do usuário alvo a cada 12 horas."""
    try:
        target_user = await bot.fetch_user(TARGET_USER_ID)
        
        if target_user.avatar:
            avatar_url = target_user.avatar.url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        avatar_bytes = await response.read()
                        await bot.user.edit(avatar=avatar_bytes)
                        print(f"✅ Avatar sincronizado com {target_user.name}!")
                    else:
                        print(f"❌ Erro ao baixar avatar: HTTP {response.status}")
        else:
            print(f"⚠️ Usuário {target_user.name} não tem avatar personalizado")
            
    except discord.HTTPException as e:
        # Rate limit ou erro de API (Discord limita mudanças de avatar)
        print(f"❌ Erro HTTP ao atualizar avatar: {e}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar avatar: {e}")


@sync_avatar.before_loop
async def before_sync_avatar():
    """Aguarda o bot estar pronto antes de iniciar o loop."""
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    """Evento disparado quando o bot está pronto."""
    print(f"{'='*50}")
    print(f"🌴 Ipod Turco está ON, visse! 🌴")
    print(f"Logado como: {bot.user.name}")
    print(f"ID: {bot.user.id}")
    print(f"{'='*50}")
    
    # Inicia a task de sincronização de avatar
    if not sync_avatar.is_running():
        sync_avatar.start()
        print("🔄 Task de sincronização de avatar iniciada (a cada 12h)")
    
    # Executa a primeira sincronização imediatamente
    await sync_avatar()
    
    # Define status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="os abestados | @me"
        )
    )


@bot.event
async def on_message(message: discord.Message):
    """Processa mensagens recebidas."""
    # Ignora mensagens do próprio bot
    if message.author == bot.user:
        return
    
    # Verifica se é DM ou se o bot foi mencionado
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    
    if not is_dm and not is_mentioned:
        # Processa comandos normais se houver
        await bot.process_commands(message)
        return
    
    # Remove a menção do bot da mensagem se houver
    user_message = message.content
    if is_mentioned:
        user_message = user_message.replace(f"<@{bot.user.id}>", "").strip()
        user_message = user_message.replace(f"<@!{bot.user.id}>", "").strip()
    
    # Se a mensagem estiver vazia após remover menção
    if not user_message:
        user_message = "oi"
    
    # Mostra "Digitando..." enquanto processa
    async with message.channel.typing():
        conversation_key = get_conversation_key(message)
        response = await get_gemini_response(user_message, conversation_key)
    
    # Divide resposta se for muito longa (limite do Discord: 2000 caracteres)
    if len(response) > 2000:
        chunks = [response[i:i+1990] for i in range(0, len(response), 1990)]
        for chunk in chunks:
            await message.reply(chunk)
    else:
        await message.reply(response)
    
    # Processa comandos
    await bot.process_commands(message)


@bot.command(name="limpar")
async def clear_history(ctx):
    """Limpa o histórico de conversa do usuário."""
    if isinstance(ctx.channel, discord.DMChannel):
        key = f"dm_{ctx.author.id}"
    else:
        key = f"channel_{ctx.channel.id}_{ctx.author.id}"
    
    conversation_history[key] = []
    await ctx.reply("Pronto meu amor, limpei minha memória sobre você... Quem é você mesmo? 🤔💅")


@bot.command(name="sobre")
async def about(ctx):
    """Informações sobre o bot."""
    embed = discord.Embed(
        title="🌴 Ipod Turco 🌴",
        description="O bot mais arretado e sarcástico do Discord, visse!",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="💅 Personalidade",
        value="Recifense, irônico, LGBT e orgulhoso!",
        inline=False
    )
    embed.add_field(
        name="🤖 Como usar",
        value="Me mencione ou mande DM que eu respondo (com má vontade, claro)",
        inline=False
    )
    embed.add_field(
        name="📝 Comandos",
        value="`!limpar` - Limpa o histórico\n`!sobre` - Essa mensagem aqui",
        inline=False
    )
    embed.set_footer(text="Feito com ☕ e sarcasmo em Recife")
    
    await ctx.reply(embed=embed)


def main():
    """Função principal para iniciar o bot."""
    if not DISCORD_TOKEN:
        print("❌ ERRO: DISCORD_TOKEN não encontrado no arquivo .env")
        return
    
    if not GEMINI_API_KEY:
        print("❌ ERRO: GEMINI_API_KEY não encontrado no arquivo .env")
        return
    
    print("🚀 Iniciando o bot...")
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
