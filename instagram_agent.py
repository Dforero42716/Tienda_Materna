import asyncio
from datetime import date
from browser_use import Agent, Browser, BrowserConfig
import os
from langchain_openai import ChatOpenAI

from env_loader import load_env
from modules.analisis import (
    total_productos,
    producto_mas_caro,
    producto_mas_barato,
    valor_total_inventario,
)

load_env()

async def responder_instagram():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Configura DEEPSEEK_API_KEY en .env antes de iniciar el agente.")

    llm = ChatOpenAI(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        api_key=api_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

    contexto_inventario = f"""
Eres el asistente de ventas de Mundo Materno, tienda de ropa materna.
Hoy es {date.today().isoformat()}.

DATOS REALES:
- Total productos: {total_productos()}
- Producto más caro: {producto_mas_caro()[0]} (${producto_mas_caro()[1]:,.0f})
- Producto más barato: {producto_mas_barato()[0]} (${producto_mas_barato()[1]:,.0f})
- Capital en inventario: ${valor_total_inventario():,.0f} COP

REGLAS:
- Solo habla de productos reales del inventario.
- No inventes precios ni stock.
- Sé amable y breve.
- Si no tienes información, di que consultarás pronto.
"""

    browser = Browser(
        config=BrowserConfig(
            headless=False,
        )
    )

    agent = Agent(
        task=f"""
Abre Instagram en https://www.instagram.com/direct/inbox/
Lee los mensajes no respondidos.
Para cada mensaje:
1. Identifica si es pregunta sobre productos, precios o disponibilidad.
2. Responde con datos reales del inventario.
3. Si no es sobre productos responde: "Hola, somos Mundo Materno. ¿En qué te podemos ayudar?"

{contexto_inventario}
""",
        llm=llm,
        browser=browser,
        use_vision=False
    )

    print("🤖 Agente de Instagram iniciado...")
    print("📱 Abriendo Chrome e Instagram...")
    await agent.run()
    await browser.close()

if __name__ == "__main__":
    asyncio.run(responder_instagram())
