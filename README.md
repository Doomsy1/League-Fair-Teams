# League of Legends Team Builder

## Overview

**League of Legends Team Builder** is a Flask-based web application designed to help users create balanced and fair teams for the popular game, League of Legends. The application allows users to add summoners by their game name and tag line, fetches their profile details and icons from Riot's APIs, and assists in creating balanced teams based on players' Matchmaking Rating (MMR).

## Features

- **Add Summoners:**
  - Input summoner names along with their game names and tag lines to add them to the application.
  - Automatically fetch and store summoners' profile icons locally using Riot's Data Dragon API.

- **Display Summoner Details:**
  - Show each summoner's name, level, MMR, and rank.
  - Display profile icons fetched and stored locally.

- **Team Management:**
  - **Drag-and-Drop Functionality:** Easily assign summoners to different teams using an intuitive drag-and-drop interface powered by SortableJS.
  - **Remove Summoners:** Remove summoners from teams with a single click.

- **Automatic Team Balancing:**
  - Balance teams based on summoners' MMR to ensure fair gameplay.
  - Prevents teams from exceeding 5 players each.
  - Handles edge cases, such as balancing with only one player.

- **PUUID Integration:**
  - Retrieve and store summoners' PUUIDs for future API requests, enhancing data accuracy and functionality.
  - Fetch and display summoners' levels using their PUUID.

## Installation

### Prerequisites

- **Python 3.7 or higher**
- **Git**
- **Virtual Environment (optional but recommended)**

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/league-fair-teams-web.git
   cd league-fair-teams-web
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the root directory and add your Riot API key:

   ```plaintext
   RIOT_API_KEY=your_actual_api_key_here
   ```

   **Important:** Replace `your_actual_api_key_here` with your actual Riot API key. **Do not** commit this file to version control.

5. **Initialize the Database**

   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

6. **Run the Application**

   ```bash
   python run.py
   ```

7. **Access the Application**

   Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Usage

1. **Add a Summoner**

   - Enter the summoner's game name and tag line in the input form.
   - Click "Add Summoner" to fetch and display the summoner's details, including their profile icon, level, MMR, and rank.

2. **Manage Teams**

   - **Drag-and-Drop:** Click and drag summoners between Team 1 and Team 2.
   - **Remove Summoners:** Click the "✖" button next to a summoner to remove them from the team.

3. **Balance Teams**

   - Click the "Balance Teams" button to automatically distribute summoners into balanced teams based on their MMR.
   - The application ensures that neither team exceeds 5 players and handles scenarios with fewer players gracefully.

## API Integration

- **Data Dragon API:** Utilized to fetch the latest version of game assets and summoners' profile icons.
- **Riot Games API:** Used to retrieve summoner details, including PUUID, level, and rank.

## Project Structure

```
league-fair-teams-web/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── utils.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── styles.css
│       └── script.js
├── migrations/
│   └── ... (Flask-Migrate files)
├── venv/
│   └── ... (Virtual environment files)
├── .env
├── requirements.txt
├── run.py
└── README.md
```

## Dependencies

- **Flask:** Web framework for Python.
- **Flask-SQLAlchemy:** ORM for database interactions.
- **Flask-Migrate:** Handles database migrations.
- **Requests:** Makes HTTP requests to external APIs.
- **python-dotenv:** Loads environment variables from `.env` files.
- **SortableJS:** Enables drag-and-drop functionality on the frontend.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add some feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

   Describe your changes and submit the pull request for review.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [Riot Games](https://developer.riotgames.com/) for providing the APIs.
- [SortableJS](https://sortablejs.github.io/Sortable/) for the drag-and-drop library.
- [Data Dragon](https://developer.riotgames.com/docs/lol) for game assets.