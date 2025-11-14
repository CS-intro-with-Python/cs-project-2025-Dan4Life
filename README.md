[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DESIFpxz)
# MindSpace

## Description

MindSpace is a **privacy-focused digital journal** that helps users reflect on their thoughts and emotions safely. Users can write journal entries through a simple web interface. Each entry is stored securely in a private database and analyzed for **sentiment (positive, neutral, or negative)**. Over time, users can view emotional trend visualizations, helping them understand their mental state and habits. It’s your mind’s safe space, no one else can read it.

***

## Setup (How to Deploy and Run)

This project uses **Docker Compose** to manage the multi-container application (web server and database) for local development, and utilizes a CI/CD pipeline for deployment.

### Prerequisites

* Docker and Docker Compose installed.

### Local Run with Docker Compose

1.  **Build and Run**: Run the following command from the project root directory. This builds the application and database images and starts all services in detached mode.
    ```bash
    docker-compose up --build -d
    ```
2.  **Access the Application**: The application server and client interface will be available at `http://localhost:8080`.
3.  **Access the API Documentation**: The Swagger documentation will be available at `http://localhost:8080/docs`.
4.  **Stop Services**:
    ```bash
    docker-compose down
    ```

### Deployment (CI/CD)

The project uses **GitHub Actions** for Continuous Integration (CI) and **Railway.com** for Continuous Deployment (CD).

* Any push to the **main** branch automatically triggers the CI pipeline, which runs the full test suite.
* Upon successful CI, the updated image is automatically deployed to the Railway service.

***

## How to Run Tests

**Tests are a core requirement of the final project**. They are run automatically via the **GitHub Actions** CI pipeline.

### Local Test Execution

1.  **Run All Tests (Unit and Integration)**: This command executes the full test suite (`pytest`) inside the running `web` container.
    ```bash
    docker-compose exec web pytest tests/
    ```

### Client Route Check (CI/CD Verification)

1.  **Execute Client Route Check**: This command executes the client script (`client/check_status.py`) inside the running `web` container, using the **requests library** to check the `/api/status` route and verify server functionality.
    ```bash
    docker-compose exec web python backend/client/check_status.py
    ```

***

## How to Get Logs

To monitor the health and behavior of the running application container:

1.  **View Live Logs**:
    ```bash
    docker-compose logs -f web
    ```
2.  **View Past Logs**:
    ```bash
    docker-compose logs web
    ```

***

## Requirements (Technologies Used)

The following technologies and tools are used in this project:

* **Language & Backend Framework:** Python (3.11-slim) and **Flask** framework.
* **Database (NoSQL):** **MongoDB** integrated and managed via Docker Compose.
* **API Documentation:** **Swagger** (using Flask-RESTX or similar tool) for documentation of all REST API endpoints.
* **Data Models & Access:** **Pymongo** or **MongoEngine** for interaction with MongoDB.
* **Machine Learning:** HuggingFace Transformers or TextBlob for sentiment analysis.
* **Testing:** **Pytest** for unit and integration testing.
* **Frontend:** HTML, JavaScript, Tailwind CSS (browser-based interface).
* **Containerization:** **Docker** and **Docker Compose**.
* **CI/CD:** **GitHub Actions** for CI and **Railway.com** for CD.

## Features

* **Private Journaling** – Create, edit, and delete personal journal entries securely.
* **Sentiment Analysis** – Each entry is analyzed for mood (positive, neutral, or negative).
* **Mood Dashboard** – View mood trends and weekly emotional stats.
* **Tags & Search** – Add tags and search or filter past entries easily.
* **Data Export** – Download all entries as a text or CSV file.
* **User Authentication** – Secure login and registration using JWT.

***

## Git

* The **main** branch will store the latest stable version of the application.
* Development and new features will be implemented in the `dev` branch before merging into `main`.

## Success Criteria

* **Functional API** - All core endpoints for authentication, journaling, and sentiment analysis work correctly.
* **Accurate Sentiment Results** - The system classifies moods reliably for most entries.
* **Smooth User Experience** - Users can write, search, and view entries easily from the web interface.
* **Data Security** - All user data is stored privately and protected with authentication and encryption.
* **Final Project Success**: All project requirements, including integrated database, API documentation (Swagger), and passing tests (Pytest), must be fully implemented and functional.
