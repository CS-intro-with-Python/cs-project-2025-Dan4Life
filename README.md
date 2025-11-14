[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DESIFpxz)
# CS_2025_project

## Description

MindSpace is a privacy-focused digital journal that helps users reflect on their thoughts and emotions safely.
Users can write journal entries through a simple web interface.
Each entry is stored securely in a private database and analyzed for sentiment (positive, neutral, or negative).
Over time, users can view emotional trend visualizations, helping them understand their mental state and habits.
[cite_start]It’s your mind’s safe space, no one else can read it. [cite: 16]

## Setup (How to Deploy and Run)

[cite_start]This project uses **Docker Compose** for local development and a containerized deployment to **Railways**. [cite: 6, 9, 17]

### Local Run with Docker Compose

1.  **Build and Run**: Run the following command from the project root directory. This builds the image and starts the `web` service.
    ```bash
    docker-compose up --build -d
    ```
2.  **Access the Application**: The application server will be available at `http://localhost:8080`.
3.  **Stop Services**:
    ```bash
    docker-compose down
    ```

### Deployment (CI/CD)

[cite_start]The project uses **GitHub Actions** for Continuous Integration (CI) and **Railway.com** for Continuous Deployment (CD). [cite: 8, 9, 46]

* Any push to the `main` branch automatically triggers the CI pipeline.
* Upon successful CI (build, run, and route checks passing), the updated image is automatically deployed to the Railway service.

## How to Run Tests

Tests are run automatically via the GitHub Actions pipeline. [cite_start]For local testing, you can use `docker-compose` to execute the commands inside the running container. [cite: 18]

### Local Test Execution (Requires containers to be running)

1.  **Execute Client Route Check**: This command runs the simple route check script (`client/check_status.py`) which uses the `requests` library to verify the `/api/status` endpoint.
    ```bash
    docker-compose exec web python client/check_status.py
    ```

## How to Get Logs

[cite_start]To monitor the health and behavior of the application, you can view the container logs. [cite: 20]

1.  **View Live Logs**:
    ```bash
    docker-compose logs -f web
    ```
2.  **View Past Logs**:
    ```bash
    docker-compose logs web
    ```

## Requirements (Technologies Used)

[cite_start]The following technologies and tools are used in this project: [cite: 19]

* [cite_start]**Language & Backend Framework:** Python (3.11-slim) and **Flask** framework. [cite: 10]
* [cite_start]**Containerization:** **Docker** and **Docker Compose**. [cite: 6]
* [cite_start]**CI/CD:** **GitHub Actions** for CI and **Railway.com** for CD. [cite: 8, 9, 46]
* [cite_start]**Database:** To be added (Future integration will include an SQL or NoSQL solution). [cite: 13]
* [cite_start]**Frontend:** HTML, JavaScript, Tailwind CSS (simplest browser-based interface). [cite: 14]
* [cite_start]**API Documentation:** To be added (Future integration will use tools like **Swagger**). [cite: 12]
* [cite_start]**Testing:** Python's standard `requests` library for route checks, and plans for unit tests using `pytest`. [cite: 11]

## Features

* **Private Journaling** – Create, edit, and delete personal journal entries securely.
* **Sentiment Analysis** – Each entry is analyzed for mood (positive, neutral, or negative).
* **Mood Dashboard** – View mood trends and weekly emotional stats.
* **Tags & Search** – Add tags and search or filter past entries easily.
* **Data Export** – Download all entries as a text or CSV file.
* **User Authentication** – Secure login and registration.

## Git

* [cite_start]The **main** branch will store the latest stable version of the application. [cite: 7]
* Development and new features will be implemented in the `dev` branch before merging into `main`.

## Success Criteria

* **Functional API** - All core endpoints for authentication, journaling, and sentiment analysis work correctly.
* **Accurate Sentiment Results** - The system classifies moods reliably for most entries.
* **Smooth User Experience** - Users can write, search, and view entries easily from the web interface.
* **Data Security** - All user data is stored privately and protected with authentication and encryption.
* [cite_start]**Checkpoint Success**: The GitHub Actions pipeline status must be successful, verifying that the Docker image builds, runs, and that existing routes are accessible.