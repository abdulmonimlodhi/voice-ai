// frontend/src/App.jsx
import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function App() {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  // WebSocket connection
  const connectWebSocket = () => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws");

    socketRef.current.onopen = () => {
      console.log("✅ Connected to backend");
    };

    socketRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      // AI TEXT
      if (msg.type === "text") {
        setMessages((prev) => [
          ...prev,
          { role: "ai", text: msg.data },
        ]);
      }

      // AUDIO
      if (msg.type === "audio") {
        try {
          const binaryString = atob(msg.data);
          const bytes = new Uint8Array(binaryString.length);

          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }

          const blob = new Blob([bytes], { type: "audio/mpeg" });
          const url = URL.createObjectURL(blob);

          const audio = new Audio(url);
          audio.play().catch((err) => {
            console.log("Audio play blocked:", err);
          });
        } catch (err) {
          console.log("Audio error:", err);
        }
      }
    };

    socketRef.current.onclose = () => {
      console.log("❌ Disconnected, reconnecting...");
      setTimeout(connectWebSocket, 2000);
    };
  };

  useEffect(() => {
    connectWebSocket();
    return () => socketRef.current?.close();
  }, []);

  // Speech recognition
  const startListening = () => {
    const recognition = new window.webkitSpeechRecognition();

    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;

      // USER MESSAGE
      setMessages((prev) => [
        ...prev,
        { role: "user", text: transcript },
      ]);

      if (socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(transcript);
      }
    };
  };

  return (
    <div
      style={{
        maxWidth: 700,
        margin: "50px auto",
        textAlign: "center",
        fontFamily: "Arial",
      }}
    >
      <h1>🎤 Voice AI (Gemini + LangGraph)</h1>

      {/* CHAT UI */}
      <div style={{ textAlign: "left", marginBottom: 20 }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
              padding: 12,
              borderRadius: 10,
              background:
                msg.role === "user" ? "#f3f3f3" : "#e8f4ff",
              lineHeight: "1.6",
            }}
          >
            <strong>
              {msg.role === "user" ? "You" : "AI"}:
            </strong>

            <div style={{ marginTop: 6 }}>
              {msg.role === "ai" ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.text}
                </ReactMarkdown>
              ) : (
                msg.text
              )}
            </div>
          </div>
        ))}
      </div>

      {/* BUTTON */}
      <button
        onClick={startListening}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        🎙️ Speak
      </button>
    </div>
  );
}