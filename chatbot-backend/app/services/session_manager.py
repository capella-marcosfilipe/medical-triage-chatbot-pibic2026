"""Session management for patient data."""
import uuid
from typing import Dict, Optional, List
from app.models.schemas import FichaDeAtendimento, PacienteData, DadosFisiologicos


class SessionManager:
    """Manage patient sessions and their data."""
    
    def __init__(self):
        self.sessions: Dict[str, FichaDeAtendimento] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.chat_jobs: Dict[str, str] = {}
    
    def create_session(self, paciente_data: PacienteData) -> str:
        """Create a new session for a patient."""
        session_id = str(uuid.uuid4())
        ficha = FichaDeAtendimento(
            session_id=session_id,
            nome_completo=paciente_data.nome_completo,
            endereco=paciente_data.endereco,
            idade=paciente_data.idade
        )
        self.sessions[session_id] = ficha
        self.conversation_history[session_id] = []
        return session_id
    
    def get_session(self, session_id: str) -> Optional[FichaDeAtendimento]:
        """Retrieve a session by ID."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, ficha: FichaDeAtendimento) -> None:
        """Update session data."""
        self.sessions[session_id] = ficha
    
    def add_smartwatch_data(self, session_id: str, dados: DadosFisiologicos) -> None:
        """Add smartwatch data to a session."""
        if session_id in self.sessions:
            self.sessions[session_id].dados_fisiologicos = dados
    
    def add_conversation_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append({
            "role": role,
            "content": content
        })
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get the conversation history for a session."""
        return self.conversation_history.get(session_id, [])

    def register_chat_job(self, job_id: str, chat_id: str) -> None:
        """Track which chat_id belongs to a queued job."""
        self.chat_jobs[job_id] = chat_id

    def get_chat_id_by_job(self, job_id: str) -> Optional[str]:
        """Resolve the chat conversation identifier for a queued job."""
        return self.chat_jobs.get(job_id)


# Global session manager instance
session_manager = SessionManager()
