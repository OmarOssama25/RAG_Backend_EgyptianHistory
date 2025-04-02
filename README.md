# Egyptian History RAG System with Gemini 2.0 Flash

A Retrieval-Augmented Generation (RAG) system for querying large Egyptian history PDF documents, powered by Gemini 2.0 for language generation and Sentence Transformers for embeddings.

## Key Features

- **Gemini 2.0 Integration**: Uses Google's latest Gemini 2.0 Flash model for high-quality responses
- **Flask API**: Model services hosted locally for efficient reuse
- **Large PDF Handling**: Optimized for 1000+ page documents
- **Source Citation**: Provides references back to original document pages
- **Persistent Indexing**: Vector store maintains indexed documents between sessions

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

4. **Set up environment variables**
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_gemini_api_key
FLASK_PORT=5050
NODE_PORT=5000
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

### Main API (Node.js)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload a PDF document |
| `/api/index` | POST | Index the uploaded document |
| `/api/query` | POST | Submit a query (`{"query": "your question"}`) |
| `/api/status` | GET | Check indexing status |

### Model Services (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/llm` | POST | Generate responses (`{"prompt": "your prompt"}`) |
| `/embed` | POST | Create embeddings (`{"text": "your text"}`) |

## Usage Example

1. **Upload your Egyptian history PDF**:
```
curl -X POST -F "pdf=@path/to/document.pdf" http://localhost:5000/api/upload
```

2. **Index the document**:
```
curl -X POST http://localhost:5000/api/index
```
3. **Query the system**:
```
curl -X POST -H "Content-Type: application/json" -d '{"query":"Who built the Great Pyramid of Giza?"}' http://localhost:5000/api/query
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
"max_tokens": 1024
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

## Project Structure
```
├── data/ # Uploaded PDF storage
├── vector_store/ # Saved vector embeddings
├── model_server.py # Flask model services
├── models/
│ ├── embedding.py # Embedding model wrapper
│ └── llm.py # Gemini 2.0 Flash interface
├── rag/
│ ├── indexer.py # PDF processing
│ ├── retriever.py # Semantic search
│ └── generator.py # Response generation
├── backend/
│ ├── server.js # Main API server
│ ├── routes/
│ │ └── api.js # API endpoints
│ ├── controllers/
│ │ └──ragController.js # Business logic
```


## License

MIT License - See [LICENSE](LICENSE) for details.


