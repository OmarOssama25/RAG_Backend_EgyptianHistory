# Egyptian History RAG System with Gemini 2.0 Flash

A Retrieval-Augmented Generation (RAG) system for querying large Egyptian history PDF documents, powered by Gemini 2.0 for language generation and Sentence Transformers for embeddings.

## Key Features

- **Gemini 2.0 Integration**: Uses Google's latest Gemini 2.0 Flash model for high-quality responses
- **Flask API**: Model services hosted locally for efficient reuse
- **Large PDF Handling**: Optimized for 1000+ page documents
- **Source Citation**: Provides references back to original document pages
- **Persistent Indexing**: Vector store maintains indexed documents between sessions
- **User Authentication**: Secure JWT-based authentication with email verification
- **Chat History Management**: Persistent conversation tracking with MongoDB

## System Architecture

```
    A[User Query] --> B[Flask API]
    B --> C[Retriever]
    C --> D[Vector Store]
    B --> E[Gemini 2.0 LLM]
    D --> E
    E --> F[Response with Sources]
```
The diagram shows:

1. **Flow Sequence**:
   - User submits query to Flask API
   - API routes request to Retriever
   - Retriever searches Vector Store
   - Results are passed to Gemini LLM
   - LLM combines context and knowledge
   - Final response with sources is returned

2. **Key Components**:
   - `Flask API`: Main request handler
   - `Retriever`: Semantic search component
   - `Vector Store`: Stored document embeddings
   - `Gemini 2.0 Flash LLM`: Response generator
   - `Response with Sources`: Final output with citations

## Prerequisites

- Python 3.8+
- Node.js 16+
- Google Cloud account (for Gemini API)
- GPU recommended (not required)
- MongoDB 6.0+ (local installation or Atlas cloud)
- MongoDB Compass (GUI recommended)

## Installation

1. **Clone the repository**

    ```
    git clone https://github.com/OmarOssama25/RAG_Backend_EgyptianHistory.git
    cd RAG_Backend_EgyptianHistory
    ```

2. **Install Python dependencies**

    ```
    pip install -r requirements.txt
    ```

3. **Install Node.js dependencies**

    ```
    npm install
    ```

4. **Install MongoDB**
    - **Windows:** Download and install from [MongoDB Community Download](https://www.mongodb.com/try/download/community)
    - **Mac (Homebrew):**
        ```
        brew tap mongodb/brew
        brew install mongodb-community
        ```
    - **Ubuntu/Linux:**
        ```
        sudo apt-get install mongodb
        ```

5. **Start MongoDB**

    - **Windows:**  
      Open Command Prompt as Administrator and run:
      ```
      net start MongoDB
      ```
    - **Mac (Homebrew):**
      ```
      brew services start mongodb-community
      ```
    - **Linux:**
      ```
      sudo systemctl start mongod
      ```

6. **Connect to MongoDB (optional, for testing)**

    ```
    mongosh "mongodb://localhost:27017/egyptian_history_rag"
    ```

7. **Set up environment variables**

    Create a `.env` file in the `backend/` directory (or root, if your setup expects it there):

    ```
    GOOGLE_API_KEY=your_gemini_api_key
    FLASK_PORT=5050
    NODE_PORT=5000
    MONGODB_URI=mongodb://localhost:27017/egyptian_history_rag
    JWT_SECRET=your_random_secure_jwt_secret
    EMAIL_SERVICE=smtp.ethereal.email
    EMAIL_USER=your_email@example.com
    EMAIL_PASSWORD=your_email_password
    EMAIL_FROM=no-reply@egyptianhistory.com
    ```

8. **Verify MongoDB Connection**

    - You can use [MongoDB Compass](https://www.mongodb.com/products/compass) for a GUI.
    - Or test in the shell:
      ```
      mongosh "mongodb://localhost:27017/egyptian_history_rag"
      show dbs
      ```

## Running the System

### Start the Flask Model Services (Port 5050)

1. **First Terminal**:
```
python model_server.py
```
This will start:
- Gemini 2.0 LLM service at `http://localhost:5050/llm`
- Embedding service at `http://localhost:5050/embed`

### Start the Node.js Server (Port 5000)

2. **Second Terminal**:
```
npm start
```

The main API will be available at `http://localhost:5000`

## API Endpoints

### Authentication API

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|-------------|
| `/api/auth/signup` | POST | Register a new user | `{"email": "user@example.com", "password": "SecurePassword123"}` |
| `/api/auth/verify/{token}` | GET | Verify user email address | N/A |
| `/api/auth/login` | POST | Login with credentials | `{"email": "user@example.com", "password": "SecurePassword123"}` |

### Chat/Conversation API

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|-------------|
| `/api/chat/conversations` | POST | Create new conversation | `{"title": "Egyptian Pyramids", "message": "Tell me about the Great Pyramid of Giza"}` |
| `/api/chat/conversations` | GET | List all user conversations | N/A |
| `/api/chat/conversations/{id}` | GET | Get specific conversation with messages | N/A |
| `/api/chat/conversations/{id}/messages` | POST | Add message to conversation | `{"role": "user", "content": "Tell me more about Giza"}` |
| `/api/chat/conversations/{id}/permanent` | DELETE | Delete conversation permanently | N/A |

### RAG System API

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|-------------|
| `/api/upload` | POST | Upload a PDF document | Form data with `pdf` file |
| `/api/index` | POST | Index the uploaded document | `{"filename": "egyptian_history.pdf"}` |
| `/api/status` | GET | Check indexing status | N/A |
| `/api/query` | POST | Submit a query | `{"query": "What do you know about Alexandria?", "conversationId": "id"}` |

### Model Services API (Flask)

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|-------------|
| `/llm` | POST | Generate responses | `{"prompt": "your prompt"}` |
| `/embed` | POST | Create embeddings | `{"text": "your text"}` |

## Authentication Details

The system uses JWT (JSON Web Tokens) for authentication:

- **Token Format**: Bearer token in Authorization header
- **Token Lifespan**: 7 days by default (configurable in `.env`)
- **Email Verification**: Required before login is permitted
- **Password Requirements**: Minimum 8 characters with numbers and letters

Example authentication header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Usage Examples

### Authentication Flow

1. **Register a new user**:
```
curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "SecurePassword123"}' http://localhost:5000/api/auth/signup
```

2. **Verify email** (link sent to user's email):
```
# User clicks verification link or you can test with:
curl -X GET http://localhost:5000/api/auth/verify/{verification_token}
```

3. **Login to get JWT token**:
```
curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "SecurePassword123"}' http://localhost:5000/api/auth/login
```

### RAG System Usage

1. **Upload your Egyptian history PDF**:
```
curl -X POST -F "pdf=@path/to/document.pdf" http://localhost:5000/api/upload
```

2. **Index the document**:
```
curl -X POST -H "Content-Type: application/json" -d '{"filename": "egyptian_history.pdf"}' http://localhost:5000/api/index
```

3. **Query the system**:
```
curl -X POST -H "Content-Type: application/json" -d '{"query":"Who built the Great Pyramid of Giza?"}' http://localhost:5000/api/query
```

### Chat System Usage

1. **Create a new conversation**:
```
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN" -d '{"title": "Egyptian Pyramids", "message": "Tell me about the Great Pyramid of Giza"}' http://localhost:5000/api/chat/conversations
```

2. **Get all conversations**:
```
curl -X GET -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/chat/conversations
```

3. **Add message to conversation**:
```
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN" -d '{"role": "user", "content": "Tell me more about hieroglyphics"}' http://localhost:5000/api/chat/conversations/{conversation_id}/messages
```

## Configuration Options

Modify `config.json` to adjust system behavior:
```
{
  "chunk_size": 500,
  "chunk_overlap": 100,
  "top_k": 5,
  "temperature": 0.7,
  "embedding_batch_size": 32,
  "max_tokens": 1024,
  "jwt_expiration": "7d",
  "verification_expiry": "24h"
}
```

## Troubleshooting

**Common Issues**:

1. **Gemini API Errors**:
   - Verify your Google Cloud API key has Gemini enabled
   - Check quota limits in Google Cloud Console

2. **Indexing Fails on Large PDFs**:
   - Reduce `chunk_size` in config.json
   - Increase `embedding_batch_size`

3. **Port Conflicts**:
   - Change ports in `.env` file if 5050/5000 are occupied

4. **CUDA Out of Memory**:
   - Restart the Flask service to clear memory
   - Reduce batch sizes in config

5. **Authentication Issues**:
   - Check that JWT_SECRET is properly set in .env
   - Verify email verification process is working
   - Ensure token is being passed correctly in Authorization header

## Project Structure
```
RAG_Backend_EgyptianHistory/
├── backend/
│   ├── config/
│   │   └── database.js                # MongoDB connection setup
│   ├── controllers/
│   │   ├── authController.js          # Signup, login, verification
│   │   ├── chatController.js          # Chat history logic
│   │   └── ragController.js           # RAG business logic (PDF, query, index)
│   ├── middleware/
│   │   └── auth.js                    # JWT authentication middleware
│   ├── models/
│   │   ├── user.js                    # User schema
│   │   ├── conversation.js            # Conversation schema
│   │   └── message.js                 # Message schema
│   ├── routes/
│   │   ├── api.js                     # RAG endpoints (upload, index, query)
│   │   ├── auth.js                    # Auth endpoints (signup, login)
│   │   └── chat.js                    # Chat endpoints (conversations, messages)
│   ├── services/
│   │   └── emailService.js            # Email utility (Ethereal/dev or real SMTP)
│   ├── server.js                      # Main Express app entry point
│   └── .env                           # Environment variables (not committed)
│
├── data/                              # Uploaded PDF storage
├── vector_store/                      # Saved vector embeddings
├── model_server.py                    # Flask app for Gemini 2.0 & embeddings
├── models/
│   ├── embedding.py                   # Embedding model wrapper
│   └── llm.py                         # Gemini 2.0 Flash interface
├── rag/
│   ├── contextual_processor.py        # Adds document context to chunks
│   ├── classifier.py                  # Prompt type classification
│   ├── indexer.py                     # PDF chunking/indexing
│   ├── retriever.py                   # Semantic search
│   └── generator.py                   # Response generation
├── requirements.txt                   # Python dependencies
├── package.json                       # Node.js dependencies & scripts
├── README.md                          # Project documentation
└── .gitignore                         # Files/folders to ignore in git
```

## License

MIT License - See [LICENSE](LICENSE) for details.

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/29393552/9384ba24-2c67-4c12-ba5f-3d6a94424585/Egyptian-History-RAG-API.postman_collection.json
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/29393552/393138e2-85cf-4a73-9fea-a4a06c1b54c1/README.md

---
Answer from Perplexity: pplx.ai/share

## License

MIT License - See [LICENSE](LICENSE) for details.


