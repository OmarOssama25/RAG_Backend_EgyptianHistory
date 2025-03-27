# Egyptian History RAG System with Gemini 2.0

A Retrieval-Augmented Generation (RAG) system for querying large Egyptian history PDF documents, powered by Gemini 2.0 for language generation and Sentence Transformers for embeddings.

## Key Features

- **Gemini 2.0 Integration**: Uses Google's latest Gemini 2.0 model for high-quality responses
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
   - `Gemini 2.0 LLM`: Response generator
   - `Response with Sources`: Final output with citations

## Prerequisites

- Python 3.8+
- Node.js 16+
- Google Cloud account (for Gemini API)
- GPU recommended (not required)

## Installation

1. **Clone the repository**

```
git clone https://github.com/yourusername/egyptian-history-rag.git
cd egyptian-history-rag
```
