# Finance Knowledge Graph

A comprehensive system for building and managing a knowledge graph of financial data, with advanced validation, quality control, and visualization capabilities.

## Features

- Entity and relationship extraction from financial documents
- Advanced validation rules for various financial domains
- Quality control and metrics tracking
- Interactive visualizations
- Batch processing capabilities
- Automated correction strategies

## Prerequisites

- Python 3.8 or higher
- Neo4j Database
- Redis Server
- Tesseract OCR (for document processing)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd finance-knowledge-graph
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Update the `.env` file with your specific configuration values.

## Project Structure

```
finance-knowledge-graph/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── validation_service.py
│   │   │   ├── quality_control.py
│   │   │   ├── validation_pipeline.py
│   │   │   ├── neo4j_service.py
│   │   │   └── celery_service.py
│   │   ├── models/
│   │   └── routers/
│   └── main.py
├── data/
│   ├── uploads/
│   └── processed/
├── logs/
├── requirements.txt
├── setup.sh
└── .env
```

## Usage

1. Start the API server:
```bash
source venv/bin/activate
uvicorn backend.main:app --reload
```

2. Start the Celery worker:
```bash
celery -A backend.app.services.celery_service worker --loglevel=info
```

3. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Validation Endpoints
- `POST /validate/entity` - Validate an entity
- `POST /validate/relationship` - Validate a relationship
- `GET /validate/rules` - Get validation rules
- `POST /validate/rules` - Update validation rules
- `GET /validate/quality` - Get quality metrics
- `GET /validate/summary` - Get validation summary

### Visualization Endpoints
- `GET /visualize/quality/trends` - View quality metric trends
- `GET /visualize/quality/benchmarks` - View quality benchmarks
- `GET /visualize/quality/impact` - View quality impact analysis
- `GET /visualize/validation/results` - View validation results
- `GET /visualize/validation/corrections` - View suggested corrections
- `GET /visualize/quality/heatmap` - View quality metrics heatmap
- `GET /visualize/quality/3d` - View 3D quality metrics visualization
- `GET /visualize/quality/sunburst` - View quality metrics hierarchy
- `GET /visualize/quality/parallel` - View parallel coordinates plot
- `GET /visualize/quality/network` - View quality metrics network
- `GET /visualize/quality/dashboard` - View comprehensive quality dashboard

### Batch Processing Endpoints
- `POST /validate/batch` - Validate a batch of entities
- `POST /validate/batch/correct` - Apply corrections to a batch
- `GET /validate/batch/status/{batch_id}` - Get batch status
- `GET /validate/batch/history` - Get batch history
- `GET /validate/batch/summary` - Get batch summary

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.


#################
#################

Functional Requirements Document: Document Intelligence Platform
1. Introduction
1.1. Purpose
This document outlines the functional requirements for the "Document Intelligence Platform." The platform is designed to ingest PDF documents, process them to extract knowledge, and provide an intelligent query interface. This document is intended for the development team to guide the implementation of the application and will serve as the primary README file for the project.

1.2. Scope
The scope of this project is to create a web-based application with a distinct frontend and backend. The application will leverage IBM's Docling for document parsing, LangChain for orchestrating AI tasks, a Large Language Model (LLM) for knowledge extraction, and a Neo4j graph database for storing and querying the extracted knowledge. The primary features include PDF-to-knowledge-graph conversion and a GraphRAG interface for natural language querying.

1.3. Overview
The Document Intelligence Platform will provide users with a seamless experience to transform static PDF documents into dynamic, queryable knowledge graphs. Users will be able to upload documents, visualize the processing pipeline, and interact with the extracted knowledge through an intuitive chat interface. The entire stack will be built using open-source technologies.

2. User Characteristics & Stories
The intended users of this platform include researchers, data analysts, students, and anyone who needs to work with complex PDF documents.

As a researcher, I want to upload a collection of academic papers so that I can ask questions about their methodologies and findings without having to re-read each one.

As a data analyst, I want to upload a financial report so that I can quickly identify all mentioned companies and their relationships to key personnel.

As a student, I want to upload my textbook chapters so that I can easily find definitions and explanations of key concepts while studying.

3. Functional Requirements
3.1. User Interface (Frontend)
The frontend shall be a single-page application (SPA) built with a modern JavaScript framework (e.g., React, Vue.js).

3.1.1. Document Upload
FR-1.1: The user shall be able to upload one or more PDF documents to the application.

FR-1.1.1: The application must only accept files with a .pdf extension.

FR-1.1.2: A reasonable file size limit (e.g., 50MB per file) shall be enforced and communicated to the user.

FR-1.2: The application shall provide a drag-and-drop area for easy file uploads.

FR-1.3: An alternative "browse files" button shall be available for users who prefer to select files from their local system.

FR-1.4: The user shall receive immediate visual feedback for each uploaded document.

FR-1.4.1: A progress bar shall be displayed during the upload process for large files.

FR-1.4.2: Once uploaded, the document shall appear in a list or grid view with its filename and initial status.

3.1.2. Pipeline Visualization
FR-2.1: For each uploaded document, the user shall be able to see a visual representation of the processing pipeline.

FR-2.2: The pipeline shall display the following stages: PDF Uploaded, Processing with Docling, Markdown Generated, Knowledge Graph Building, and GraphRAG Ready.

FR-2.3: Each stage in the pipeline shall have a clear status indicator: Pending, In Progress, Completed, or Failed.

FR-2.4: The visualization shall update in real-time without requiring a page refresh.

FR-2.4.1: If a stage fails, the indicator shall turn to Failed, and hovering over it shall display an error message.

3.1.3. Action Triggers
FR-3.1: The user shall have a button or control to initiate the processing of an uploaded document ("Process Document").

FR-3.2: The user shall be able to trigger the "Build Knowledge Graph" step independently after the Markdown has been generated. This allows users to review the Markdown before committing to graph creation.

FR-3.3: Action buttons shall be disabled when a process is already running for that document to prevent duplicate actions.

3.1.4. Document Viewer
FR-4.1: Once the Docling processing is complete, the user shall be able to view the generated Markdown content in a dedicated modal or panel.

FR-4.2: The Markdown shall be rendered in a clean, readable format.

FR-4.3: The viewer shall support standard Markdown features, including headings, lists, tables, and code blocks with syntax highlighting.

FR-4.4: The viewer shall include a search functionality to find text within the Markdown document.

3.1.5. Graph Visualization
FR-5.1: Upon completion of the knowledge graph creation, the user shall be able to view an interactive visualization of the graph.

FR-5.2: The visualization shall display nodes (entities) and edges (relationships), styled differently based on their labels (e.g., Person nodes are blue, Location nodes are green).

FR-5.3: The user shall be able to pan and zoom within the graph visualization.

FR-5.4: Clicking on a node or edge shall display its properties (e.g., name, type) in a sidebar or tooltip.

FR-5.5: The user shall be able to filter the graph by node and relationship types.

3.1.6. GraphRAG Chat Interface
FR-6.1: The application shall provide a chat interface for each document that has a generated knowledge graph.

FR-6.2: The user shall be able to type natural language questions into a text input field and submit them by pressing "Enter" or clicking a "Send" button.

FR-6.3: The conversation history (questions and answers) shall be displayed in a chronological, chat-like format.

FR-6.4: The interface shall indicate when the system is processing a query (e.g., with a typing indicator).

FR-6.5: The user shall be able to copy individual responses to the clipboard.

FR-6.6: The user shall be able to clear the conversation history.

3.2. Backend and Processing
The backend shall be a Python-based application using the FastAPI framework.

3.2.1. PDF Processing with Docling
FR-7.1: The backend shall use the IBM Docling library to parse uploaded PDF files.

FR-7.2: The processing shall extract text, tables, and layout information from the PDF.

FR-7.3: The output of the Docling processing shall be a well-structured Markdown document, which is then stored for future use.

FR-7.4: The system shall handle potential errors during Docling processing gracefully and report the failure status via the API.

3.2.2. Knowledge Graph Creation
FR-8.1: The backend shall use the generated Markdown content as the input for knowledge graph creation.

FR-8.2: The system shall use an LLM (via LangChain's LLMGraphTransformer) to extract entities and relationships.

FR-8.3: The extracted graph data shall be persisted to a Neo4j database. Re-processing a document shall update the existing graph data for that document, not create duplicates.

FR-8.4: The system shall be configurable (e.g., via a config.yaml file) to allow for different types of nodes and relationships to be extracted, enabling customization for different domains.

3.2.3. GraphRAG Engine
FR-9.1: The backend shall implement a GraphRAG engine to handle natural language queries.

FR-9.2: The engine shall be capable of translating natural language questions into Cypher queries.

FR-9.3: The engine shall use the results from the Cypher query and an LLM to generate a coherent, natural language answer. If the query returns no results, the engine shall inform the user that it could not find an answer in the document.

FR-9.4: The engine shall be implemented using LangChain's GraphCypherQAChain or a similar framework.

FR-9.5: All generated Cypher queries shall be logged for debugging and auditing purposes.

3.2.4. API Endpoints
FR-10.1: The backend shall expose a RESTful API for communication with the frontend.

FR-10.2: The API shall adhere to standard HTTP status codes for success and error states.

FR-10.3: The API shall implement the endpoints defined in the initial design, with clear request/response schemas (e.g., using Pydantic models).

4. Data Requirements
DR-1 (Data Persistence): Uploaded PDFs and generated Markdown files shall be stored on the server's file system in a structured directory format (e.g., /data/{document_id}/).

DR-2 (Neo4j Schema): Each node in the Neo4j database shall have a documentId property to associate it with its source document. This ensures that queries for one document do not return results from another.

DR-3 (Data Integrity): The system must ensure that all graph elements related to a document can be uniquely identified and managed (e.g., for deletion or updating).

5. Error Handling and Recovery
ER-1 (Upload Failure): If a file upload fails (e.g., due to network issues or invalid file type), the frontend shall display a clear and user-friendly error message.

ER-2 (Processing Failure): If any stage of the backend pipeline fails, the status shall be updated accordingly, and the specific error message shall be logged and made available to the user upon request (e.g., via a tooltip).

ER-3 (API Errors): The backend API shall return appropriate HTTP status codes (e.g., 400 for bad requests, 500 for server errors) along with a descriptive JSON error message.

6. Non-Functional Requirements (High-Level)
NFR-1 (Performance): API responses for non-processing tasks (e.g., status checks) should be completed in under 500ms. Document processing time will vary but should be reasonable, and the user should be kept informed of the progress.

NFR-2 (Scalability): The application should be containerized (e.g., using Docker) to allow for easy deployment and scaling of backend services.

NFR-3 (Security): The API shall implement basic authentication to prevent unauthorized access. User-uploaded content should be isolated.

NFR-4 (Usability): The user interface must be intuitive, requiring minimal to no training for a user to operate.

NFR-5 (Maintainability): The codebase must be well-documented with comments and adhere to standard coding conventions for Python and JavaScript. The system shall have comprehensive logging.

NFR-6 (Compatibility): The frontend application shall be compatible with the latest versions of major web browsers (Chrome, Firefox, Safari, Edge).