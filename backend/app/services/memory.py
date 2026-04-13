# backend/app/services/memory.py
"""
Simple in-memory conversation store
"""

from collections import defaultdict

# session_id → list of messages
memory_store = defaultdict(list)


def add_message(session_id: str, role: str, content: str):
    memory_store[session_id].append({
        "role": role,
        "content": content
    })


def get_messages(session_id: str):
    return memory_store[session_id]


def reset_memory(session_id: str):
    memory_store[session_id] = []