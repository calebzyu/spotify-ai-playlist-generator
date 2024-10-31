# Spotify AI Playlist Generator

A Flask-based web application that utilizes the Spotify API to generate custom playlists based on user prompts. This project leverages a large language model (LLM) to interpret user input, turning it into Spotify search queries used to recommend songs aligned with the user's specified mood, genre, artist preferences, and more.

---

## Contents
  - [Technologies Used](#technologies-used)
  - [Spotify API Setup](#spotify-api-setup)
  - [Installation](#installation)
  - [Usage](#usage)

## Technologies Used

| Technology                          | Description                                                               |
| ----------------------------------- | ------------------------------------------------------------------------- |
| JavaScript, HTML, CSS               | Front-end for user interactions.                                          |
| Flask                               | Back-end for handling requests and data processing.                       |
| Spotify API                         | Conduct Spotify search, fetch song recommendations, and curate playlists. |
| Ollama `llama3.1:70b-instruct-q2_K` | Generate creative search queries.                                         |

## Spotify API Setup

To set up the app, you will need:

1. **Client ID, Client Secret, and Redirect URI**: Obtain these from the [Spotify dashboard](https://developer.spotify.com/dashboard). They are required for API authentication.
    - In the Spotfiy dashboard, set the redirect URI to `http://localhost:8000/callback`. 
2. **Generate a Secret Key**: You can generate a secret key for the Flask app using Python's `secrets` module. Run the following to generate a key:
   
    ```python
    import secrets
    print(secrets.token_hex(16))
    ```

## Installation

1. **Clone the Repository:**
   
    ```bash
    git clone https://github.com/calebzyu/spotify-ai-playlist-generator
    cd spotify-ai-playlist-generator
    ```

2. **Set Up Environment Variables:**
    
    Create a `.env` file in the project root with the following:

    ```
    CLIENT_ID = <Spotify Client ID>
    CLIENT_SECRET = <Spotify Client Secret>
    SECRET_KEY = <Flask Secret Key>
    ```

3. **Install Dependencies:**
   
    ```bash
    conda env create -f environment.yml
    ```

4. **Run the Flask Application:**
   
    ```bash
    flask run
    ```

## Usage

1. Visit the application in your browser at `http://localhost:8000`.
2. Log in with your Spotify account to allow the app to create playlists.
3. Enter a prompt describing your desired playlist (e.g., `smooth jazz for a rainy evening`).
4. The app will generate a playlist, which you can then view in your account.
