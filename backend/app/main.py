# backend/app/main.py
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import uuid


from app.services.tts import text_to_speech
from app.agents.agent import run_agent

import base64

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Groq + LangGraph Voice AI Running 🚀"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Unique session per connection
    session_id = str(uuid.uuid4())
    print(f"✅ Client connected: {session_id}")

    try:
        while True:
            user_text = await websocket.receive_text()
            print("User:", user_text)

            # Agent call
            response = await asyncio.to_thread(
                run_agent,
                session_id,
                user_text
            )

            print("AI:", response)

            # Send text
            await websocket.send_json({
                "type": "text",
                "data": response
            })

            # TTS
            audio_bytes = await asyncio.to_thread(
                text_to_speech,
                response
            )
            print("AUDIO SIZE:", len(audio_bytes))

            if audio_bytes:
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                await websocket.send_json({
                    "type": "audio",
                    "data": audio_base64
                })

            await websocket.send_json({
                "type": "done",
                "data": response
            })

    except WebSocketDisconnect:
        print(f"❌ Client disconnected: {session_id}")

    except Exception as e:
        print("Error:", e)
        await websocket.close()