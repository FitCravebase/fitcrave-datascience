# Health and Fitness Chatbot API

This repository contains the backend API for the Nutrition and Fitness AI Agent. It is built using **FastAPI** and utilizes **LangGraph** and **Langchain** to handle natural language processing workflows, connected to a **MongoDB** database.

## Prerequisites
- Python 3.10+
- Docker (optional, for deployment)
- A `.env` file containing your API keys and configuration

## Environment Variables

Ensure you have a `.env` file at the root of the project with the following keys (example):

```ini
GEMINI_API_KEY="your_google_gemini_api_key_here"
ENVIRONMENT=development
MONGODB_URI="mongodb+srv://..."
DB_NAME=fitcrave
COLLECTION_NAME=conversations
```

## Running Locally

1. **Activate your virtual environment** (if applicable):
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at [http://localhost:8000](http://localhost:8000). You can view the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Deployment with Docker

To deploy the API inside a container, you can use the provided `Dockerfile`.

1. **Build the Docker Image**:
   ```bash
   docker build -t fitcrave-api .
   ```

2. **Run the Docker Container**:
   You can run the container and pass your `.env` file to set the required API keys and DB credentials inside the container:
   
   ```bash
   docker run -p 8000:8000 --env-file .env fitcrave-api
   ```

   The application will be accessible on port 8000 inside the container and mapped to port 8000 on your host machine.
