[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DESIFpxz)
# CS_2025_project

## Description

MindSpace is a privacy-focused digital journal that helps users reflect on their thoughts and emotions safely.
Users can write journal entries through a simple web interface.
Each entry is stored securely in a private database and analyzed for sentiment (positive, neutral, or negative).
Over time, users can view emotional trend visualizations, helping them understand their mental state and habits.
It’s your mind’s safe space, no one else can read it.

## Setup

Describe the steps to set up the environment and run the application. This can be a bash script or docker commands.

```
Your commands
#To be added

```

## Requirements

Describe technologies, libraries, languages you are using (this can be updated in the future).

* **Language:** Python (Flask framework)  
* **Database:** To be added
* **Frontend:** HTML, JavaScript, Tailwind CSS for styling  
* **Machine Learning:** HuggingFace Transformers or TextBlob for sentiment analysis  
* **Authentication:** JWT (PyJWT)  
* **Containerization:** Docker and Docker Compose  
* **CI/CD:** GitHub Actions for automated testing and deployment  


## Features

* Describe the main features the application performs.
* Private Journaling – Create, edit, and delete personal journal entries securely.
* Sentiment Analysis – Each entry is analyzed for mood (positive, neutral, or negative).
* Mood Dashboard – View mood trends and weekly emotional stats.
* Tags & Search – Add tags and search or filter past entries easily.
* Data Export – Download all entries as a text or CSV file.
* User Authentication – Secure login and registration.

## Git

Specify which branch will store the latest stable version of the application

* The main branch will store the latest stable version of the application.
* Development and new features will be implemented in the dev branch before merging into main.

## Success Criteria

Describe the criteria by which the success of the project can be determined
(this will be updated in the future)

* Functional API - All core endpoints for authentication, journaling, and sentiment analysis work correctly.
* Accurate Sentiment Results - The system classifies moods reliably for most entries.
* Smooth User Experience - Users can write, search, and view entries easily from the web interface.
* Data Security - All user data is stored privately and protected with authentication and encryption.
