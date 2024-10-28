import os
import secrets
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify, redirect, session, render_template, url_for
from flask_cors import CORS
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from langchain_ollama import OllamaLLM
from urllib.parse import quote

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
CORS(app, supports_credentials=True)

# Spotify API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
SCOPE = "playlist-modify-public,playlist-modify-private"

########################################
# /
# Initial page with login button.
########################################

@app.route("/")
def index():
  return render_template("index.html")

########################################
# /login
# Redirect user to authentication url.
########################################

@app.route("/login")
def login():
  token_info = session.get("token_info")
  # Check if token exists and is NOT expired
  if token_info and (int(time.time()) < token_info["expires_at"]):
    return redirect(url_for("main"))  # Redirect to main endpoint

  state = secrets.token_urlsafe(16)
  session["state"] = state  # Store it for validation later

  sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    state=state,
    scope=SCOPE,
    show_dialog=True,
  )

  auth_url = sp_oauth.get_authorize_url()
  return redirect(auth_url)  # Redirect to Spotify auth url.

########################################
# /callback
# Process authentication result.
########################################

@app.route("/callback")
def callback():
  # Check if authentication failed or cancelled
  error = request.args.get("error")
  if error == "access_denied":
    return redirect(url_for("index"))  # Redirect to index endpoint.

  # Validate session state
  state = request.args.get("state")
  if state != session.get("state"):
    return redirect("/error?message=state_mismatch")  # Redirect to error endpoint

  sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
  )

  code = request.args.get("code")  # Get response code
  token_info = sp_oauth.get_access_token(code)  # Get user token
  if not token_info:
    return redirect("/error?message=token_retrieval_failed")

  #  Set session expiration time
  if "expires_at" not in token_info:
    token_info["expires_at"] = int(time.time()) + token_info["expires_in"]

  session["token_info"] = token_info  # Store the token info to session

  return redirect(url_for("main"))  # Redirect to main endpoint

########################################
# /main
# Main content endpoint.
########################################

@app.route("/main")
def main():
  return render_template("main.html")

########################################
# /generate_playlist
# Generates a playlist based on user input.
########################################

@app.route("/generate_playlist", methods=["POST"])
def generate_playlist():
  try:
    # Retrieve token_info from session
    token_info = session.get("token_info")
    # Check if token exists or token is expired
    if not token_info or (int(time.time()) >= token_info["expires_at"]):
      return jsonify({"error": "user_not_authenticated"}), 401

    # Initialize Spotify client with access token
    access_token = token_info["access_token"]
    sp = Spotify(auth=access_token)

    # Get Spotify User ID
    user_id = sp.current_user()["id"]

    # Get the user input from the request
    user_input = request.json.get("userInput")

    # Get the track count from the request
    track_count = request.json.get("trackCount")
    print(track_count)

    # Generate search query using LLM
    model = OllamaLLM(model="llama3.1:8b")
    prompt = f"""
      Based on the following description, generate a precise and effective
      search query for Spotify. Be creative and include filters like track
      names, artist names, genres, or any other relevant keywords to make the
      search as effective as possible.

      You can also use Spotify-specific filters such as album, artist, track,
      year, upc, genre, tag:hipster, tag:new, and isrc. These filters should be
      used strategically to improve search accuracy.

      An example query format is 'remaster track:Doxy artist:Miles Davis
      genre:jazz'.

      Guidelines:

      Be faithful and accurate to the user prompt. If the prompt specifies
      certain songs, artists, genres, or moods, ensure these are included
      exactly as described. Prioritize clarity and relevance in the query by
      focusing on the most pertinent search terms. Avoid unnecessary words or
      details. 
      
      Return only the formatted query as plain text, with no additional symbols,
      extra text, or quotation marks. 
      
      User prompt: {user_input}
      """
    llm_query = model.invoke(prompt)
    encoded_query = quote(llm_query)  # Percent-encodes the LLM query

    # Search Spotify API
    results = sp.search(q=encoded_query, type="track,playlist", limit=track_count)
    track_ids = [track["id"] for track in results["tracks"]["items"]]

    # Create private playlist
    playlist = sp.user_playlist_create(user=user_id, name="Generated Playlist", public=False)
    sp.playlist_add_items(playlist["id"], track_ids)

    return jsonify({"playlist_url": playlist["external_urls"]["spotify"]})

  except Exception as e:
    return jsonify({
      "error": "playlist_generation_error.",
      "details": str(e),
    }), 500

########################################
# /error
# Handles some errors.
########################################

@app.route("/error")
def error():
  message = request.args.get("message", "An unexpected error occured.")
  if message == "state_mismatch":
    message = "Session state mismatch. Please try logging in again."
  elif message == "token_retrieval_failed":
    message = "Failed to retrieve token information. Please try logging in again."
  return render_template("error.html", message=message)

# if __name__ == "__main__":
#   app.run(host="localhost", port=8000, debug=True)
