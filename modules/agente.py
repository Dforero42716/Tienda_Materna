import ollama
from router import enrutar

def formatear_con_llm(datos: str, pregunta: str) -> str:
    prompt = f"""Eres el asistente de una tienda de ropa materna.
Te doy datos reales del inventario y una pregunta del usuario.
Tu único trabajo es redactar una respuesta clara y amable usando SOLO los datos que te doy.
NO inventes nada. NO agregues datos que no estén aquí.

Pregunta del usuario: {pregunta}

Datos reales: {datos}

Responde en español, de forma breve y directa."""

    respuesta = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )
    return respuesta["message"]["content"]

def responder(pregunta: str) -> str:
    datos = enrutar(pregunta)

    if datos == "no entendí":
        return "No entendí tu pregunta. Puedes preguntarme por el inventario, stock, ventas o ganancias."

    return formatear_con_llm(datos, pregunta)

if __name__ == "__main__":
    print("Agente listo. Escribe 'salir' para terminar.\n")
    while True:
        pregunta = input("Tú: ")
        if pregunta.lower() == "salir":
            break
        respuesta = responder(pregunta)
        print(f"Agente: {respuesta}\n")