from app.tools.registry import Tool, tool_registry
from app.database import AsyncSessionLocal
from sqlalchemy import text # Using raw text for simple temporary note table or we can just use an in-memory dict for now as requested initially, but user said "Structure the code so persistent database storage can be added later. Initially keep notes session-based."
import uuid

# In-memory store for session notes, keyed by conversation_id
# DB integration will replace this easily since it's async.
session_notes = {}

async def create_note(conversation_id: str, content: str) -> str:
    """Creates a new note for the current conversation."""
    if conversation_id not in session_notes:
        session_notes[conversation_id] = {}
        
    note_id = str(uuid.uuid4())[:8]
    session_notes[conversation_id][note_id] = content
    return f"Note created with ID: {note_id}"

async def list_notes(conversation_id: str) -> str:
    """Lists all notes for the current conversation."""
    notes = session_notes.get(conversation_id, {})
    if not notes:
        return "You have no notes."
        
    result = "Your notes:\n"
    for note_id, content in notes.items():
        result += f"- [{note_id}]: {content}\n"
    return result

async def delete_note(conversation_id: str, note_id: str) -> str:
    """Deletes a note by its ID."""
    notes = session_notes.get(conversation_id, {})
    if note_id in notes:
        del notes[note_id]
        return f"Note {note_id} deleted."
    return f"Note {note_id} not found."

create_note_tool = Tool(
    name="create_note",
    description="Creates a new note to remember important information.",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "content": {"type": "string", "description": "The content of the note"}
        },
        "required": ["conversation_id", "content"]
    },
    callable=create_note
)

list_notes_tool = Tool(
    name="list_notes",
    description="Lists all saved notes.",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"}
        },
        "required": ["conversation_id"]
    },
    callable=list_notes
)

delete_note_tool = Tool(
    name="delete_note",
    description="Deletes a note by its ID.",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "note_id": {"type": "string", "description": "The ID of the note to delete"}
        },
        "required": ["conversation_id", "note_id"]
    },
    callable=delete_note
)

tool_registry.register(create_note_tool)
tool_registry.register(list_notes_tool)
tool_registry.register(delete_note_tool)
