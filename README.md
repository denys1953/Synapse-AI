# SynapseAI

SynapseAI is a powerful modular platform designed for AI-driven research and document analysis. It combines a robust **FastAPI** backend with a user-friendly **Streamlit** frontend, enabling users to create personal "Notebooks," upload PDF documents, index them using **ChromaDB**, and interact with them via **OpenAI** LLMs.

## 🚀 Features

- **User Authentication**: Secure registration and login using JWT tokens.
- **Notebook Management**: Organize your research into separate notebooks.
- **PDF Ingestion**: Upload PDF files and automatically extract text for AI analysis.
- **AI Chat**: Ask questions about your uploaded documents and get context-aware answers.
- **Vector Store Persistence**: Efficient document retrieval using ChromaDB.
- **History Tracking**: Keep track of your conversations within each notebook.

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy (Async), Alembic, Pydantic.
- **AI/LLM**: LangChain, OpenAI API.
- **Vector Database**: ChromaDB.
- **Frontend**: Streamlit.
- **Database**: PostgreSQL with `asyncpg`.
- **Infrastructure**: Docker, `docker-compose`, `uv` for package management.

---

## ⚙️ Setup Instructions

### Prerequisites
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- [OpenAI API Key](https://platform.openai.com/)

### 1. Environment Configuration
Create a `.env` file in the root directory and populate it with the following variables:

```env
# App Settings
SECRET_KEY=your_very_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database (PostgreSQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=synapse_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ChromaDB
CHROMADB_HOST=chroma
CHROMADB_PORT=8000

# OpenAI
OPENAI_API_KEY=sk-proj-your-key
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=false
```

### 2. Launch with Docker
Use Docker Compose to build and start all services (FastAPI, Streamlit, PostgreSQL, ChromaDB):

```bash
docker-compose up --build
```

### 3. Database Migrations
Run the migrations within the `fastapi` container to set up the database schema:

```bash
docker exec -it synapse_app uv run alembic upgrade head
```

---

## 📡 API Documentation

Once the backend is running, you can access the interactive Swagger UI at: `http://localhost:8001/docs`

### Authentication
- `POST /auth/register`: Register a new account.
- `POST /auth/login`: Authenticate and receive an access token.

### Notebooks
- `GET /notebooks/`: List all notebooks for the current user.
- `POST /notebooks/add`: Create a new notebook (requires `title`).
- `GET /notebooks/{notebook_id}/sources`: List all PDF sources uploaded to a notebook.
- `GET /notebooks/{notebook_id}/chat_history`: Retrieve past chat messages for a notebook.

### AI & Ingestion
- `POST /notebooks/source/{notebook_id}/upload`: Upload and index a PDF file for a specific notebook.
- `POST /notebooks/notebook/{notebook_id}/ask`: Ask the AI a question based on the notebook's sources.

---

## 🖥 User Interface

The SynapseAI UI is built with **Streamlit** and provides a seamless experience for non-technical users.

**Access URL:** `http://localhost:8501`

**Key UI Features:**
1. **Sidebar Navigation**: Switch between different notebooks or logout.
2. **Document Management**: Easy-to-use upload area for PDFs.
3. **Chat Interface**: A familiar chat experience to interact with your data.
4. **Source Transparency**: View which documents are currently indexed in your notebook.

---

## 📂 Project Structure

- `src/main.py`: FastAPI entry point.
- `src/auth/`: User authentication logic and routes.
- `src/notebooks/`: Core notebook and source management.
- `src/ai_providers/`: LangChain and Vector Store integrations.
- `src/frontend.py`: Streamlit frontend application.
- `alembic/`: Database migration scripts.
