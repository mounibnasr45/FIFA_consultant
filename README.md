# Fifa chatbot Application using RAG

This project implements a Retrieval-Augmented Generation (RAG) application using FastAPI. The application retrieves information from Elasticsearch and FAISS, and generates responses using a language model.

## Project Structure

```
rag-app
├── src
│   ├── main.py          # Implementation of the RAG application
│   ├── requirements.txt  # List of dependencies
│   └── Dockerfile        # Instructions for building the Docker image
├── .dockerignore         # Files to ignore when building the Docker image
└── README.md             # Documentation for the project
```

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd rag-app
   ```

2. **Install Dependencies**:
   You can install the required dependencies using pip:
   ```bash
   pip install -r src/requirements.txt
   ```

3. **Docker Setup**:
   - Ensure you have Docker installed on your machine.
   - Build the Docker image:
     ```bash
     docker build -t rag-app src/
     ```
   - Run the Docker container:
     ```bash
     docker run -d -p 8000:8000 rag-app
     ```

## Usage

Once the application is running, you can access the API endpoints:

- **Chat Endpoint**: `POST /api/chat`
  - Send a JSON payload with a question to receive an answer based on FIFA laws and regulations.

- **Search Endpoint**: `POST /api/search`
  - Send a JSON payload with a question to retrieve relevant search results.

## Testing the Deployment

You can test the API using tools like Postman or curl. For example, to test the chat endpoint:

```bash
curl -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d '{"question": "What are the sanctions for a foul?"}'
```

## Deployment to Production

For production deployment, consider using a container orchestration tool like Kubernetes. Set up monitoring and logging to track application performance and errors.

## License

This project is licensed under the MIT License.
