# AI-Powered Portfolio Manager for the Indian Market

**Version 1.0.0**

An advanced portfolio management system built with Streamlit, specifically designed for the Indian stock market. This application integrates real-time market data, AI-driven analysis via the Google Gemini API, and comprehensive portfolio analytics to provide actionable insights for investors focused on Indian equities.

---

## Table of Contents

- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Architecture](#project-architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Core Features

-   **India-Market Focus**: All analytics, data fetching, and financial calculations are tailored to the Indian market, including NSE/BSE stocks and sectoral indices, with all monetary values in INR.

-   **AI-Driven Analysis**: Utilizes Google's Gemini API to provide deep, context-aware analysis of market conditions, stock performance, and portfolio construction strategies.

-   **Interactive Dashboards**: A multi-page application structure provides dedicated interfaces for:
    -   **Market Analysis**: A real-time dashboard tracking the Nifty 50, Sensex, and key sectoral indices with live price data.
    -   **AI Portfolio Agent**: An interactive tool for generating optimized portfolios, conducting market research, and simulating trading strategies.
    -   **Data Management**: A powerful interface for querying, visualizing, and exporting market and portfolio data stored in the application's database.

-   **Quantitative Stock Screening**: A proprietary engine screens and scores Indian stocks based on **Quality, Value, Growth, and Momentum (QVGM)** metrics to identify high-potential investment opportunities.

-   **Reinforcement Learning Environment**: Includes a DRL trading environment (using OpenAI Gym and TensorFlow) to simulate and test AI-based trading strategies on historical Indian market data.

-   **Database Integration**: Features a local SQLite database for efficient data caching and persistence, with support for production-grade PostgreSQL environments.

---

## Technology Stack

| Category             | Technologies Used                                                                     |
| -------------------- | ------------------------------------------------------------------------------------- |
| **Frontend Framework** | Streamlit                                                                             |
| **AI Engine**        | Google Gemini Pro                                                                     |
| **Data Sources**     | `yfinance`, Finnhub API                                                               |
| **Data Analytics**   | Pandas, NumPy                                                                         |
| **Visualization**    | Plotly Express                                                                        |
| **Machine Learning** | TensorFlow, Keras, OpenAI Gym                                                         |
| **Database**         | SQLite (Default), PostgreSQL (Production Option)                                      |

---

## System Requirements

-   Python 3.8 or higher
-   Git version control
-   Active API Keys for:
    -   Google Gemini
    -   Finnhub

---

## Installation Guide

Execute the following commands to set up the project environment.

1.  **Clone the repository:**
    ```bash
    git clonehttps://github.com/DipayanDasgupta/ai_agent_portfolio_manager.git
    cd india-ai-portfolio-manager
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *For Windows, use: `venv\Scripts\activate`*

3.  **Install all required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration

1.  **Create the environment configuration file** from the provided template. This file stores your API keys securely and is ignored by Git.
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** with a text editor and populate it with your valid API keys.

    ```env
    # Required: Get your key from Google AI Studio (https://aistudio.google.com/app/apikey)
    GEMINI_API_KEY="your-google-gemini-api-key"

    # Required: Get your free key from Finnhub (https://finnhub.io/register)
    FINNHUB_API_KEY="your-finnhub-api-key"

    # Optional: For production-grade database. If left commented, a local SQLite DB will be used.
    # DATABASE_URL="postgresql://user:password@host:port/dbname"
    ```

---

## Running the Application

1.  **Initialize the Database:** If you are running the application for the first time or after a schema change, it is recommended to remove the old database file to ensure the correct schema is created.
    ```bash
    rm -f data/portfolio_manager.db
    ```

2.  **Launch the Streamlit server:**
    ```bash
    streamlit run app.py
    ```
    The application will be accessible in your web browser, typically at `http://localhost:8501`.

---

## Project Architecture

The codebase is organized into modular directories to separate concerns and enhance maintainability.

-   `app.py`: The main application entry point that handles routing and global component initialization.
-   `components/`: Contains the Python scripts for each user-facing page of the Streamlit application.
-   `utils/`: A collection of backend modules containing the core business logic, including data fetching, AI analysis, database management, and quantitative modeling.
-   `requirements.txt`: A list of all Python package dependencies.
-   `.env`: A local file for storing secret API keys (not tracked by Git).

---

## Contributing

We welcome contributions to enhance the functionality and performance of this application. Please follow the standard fork-and-pull-request workflow.

1.  Fork the repository.
2.  Create a new branch for your feature or bugfix.
3.  Commit your changes with clear, descriptive messages.
4.  Push your branch to your forked repository.
5.  Open a pull request against the main repository branch.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for full details.