from langchain_ollama import OllamaLLM
from spotipy import Spotify
from typing import Dict, List
from ast import literal_eval
import re

class PlaylistGenerator:

  def __init__(self, spotify: Spotify, user_input: str, track_count: int):
    """Initialize a playlist generator."""
    self.sp = spotify
    self.sp_id = self.sp.current_user()["id"]
    self.user_input = user_input
    self.track_count = track_count
    self.prompt_template = self.load_prompt_template("prompt-template.txt")
    self.prompt = self.prompt_template.format(user_input=self.user_input)
    self.model = OllamaLLM(model="llama3.1:70b-instruct-q2_K")
    
  def __call__(self):
    """Generate a Spotify playlist."""
    seeds = self.invoke_model_and_generate_seeds()
    # Set seeds[seed_type] to None if it's empty
    for seed_type in seeds:
      seeds[seed_type] = seeds[seed_type] if seeds[seed_type] else None
    playlist = self.generate_playlist(
      seed_artists=seeds["artists"],
      seed_genres=seeds["genres"],
      seed_tracks=seeds["tracks"],
    )
    return playlist

  def load_prompt_template(self, filename: str) -> str:
    """Load a prompt template from file."""
    with open(file=filename, mode="r", encoding="utf-8") as file:
      return file.read()

  def invoke_model_and_generate_seeds(self) -> Dict[str, str]:
    """
    Invoke LLM model to generate a python dictionary of artists, genres, and tracks. 
    Get seeds for each element in the model's response for the Spotify recommendations API.
    """
    response = self.model.invoke(self.prompt)  # Invoke model
    print(response)  # Debug
    response = re.sub(pattern=r"`", repl="", string=response)  # Remove backticks
    response = literal_eval(response)  # Treat output as dict
    seeds = {"artists": [], "genres": [], "tracks": []}  # Seeds to return

    # Validate genres
    if response["genres"]:
      # Get Spotify genre seeds
      rec_genre_seeds = self.sp.recommendation_genre_seeds()["genres"]
      # Validates all genres generated by the model
      seeds["genres"] = [genre for genre in response["genres"] if genre in rec_genre_seeds]

    # Search for artists
    if response["artists"]:
      # Iterate over artist queries
      for query in response["artists"]:
        # Search Spotify by artist
        results = self.sp.search(q=query, type="artist", limit=10)
        # Get Spotify ID of the first result if results exist
        if results["artists"]["items"]:
          spotify_id = results["artists"]["items"][0]["id"]
          seeds["artists"].append(spotify_id)

    # Search for tracks
    if response["tracks"]:
      # Iterate over track queries
      for query in response["tracks"]:
        # Search Spotify by track
        results = self.sp.search(q=query, type="track", limit=10)
        # Get Spotify ID of the first result if results exist
        if results["tracks"]["items"]:
          spotify_id = results["tracks"]["items"][0]["id"]
          seeds["tracks"].append(spotify_id)
    
    return seeds

  def generate_playlist(
    self,
    seed_artists: List[str] = None,
    seed_genres: List[str] = None,
    seed_tracks: List[str] = None,
  ) -> Dict:
    """Generate Spotify playlist URL based on provided seeds."""
    # Debug
    print({"seed_artists": seed_artists, "seed_genres": seed_genres, "seed_tracks": seed_tracks})
    
    # Check seed limits
    if seed_artists and len(seed_artists) > 2:
      seed_artists = seed_artists[:2]
    if seed_genres and len(seed_genres) > 1:
      seed_genres = seed_genres[:1]
    if seed_tracks and len(seed_tracks) > 2:
      seed_tracks = seed_tracks[:2]
      
    # Get Spotify recommendation results
    results = self.sp.recommendations(
      seed_artists=seed_artists,
      seed_genres=seed_genres,
      seed_tracks=seed_tracks, 
      limit=self.track_count,  # Number of tracks as requested by the user
    )

    # Get track IDs for each track in results
    track_ids = [track["id"] for track in results["tracks"]]
    # Create new playlist
    playlist = self.sp.user_playlist_create(user=self.sp_id, name="Generated Playlist", public=False)
    # Add tracks to playlist
    self.sp.playlist_add_items(playlist_id=playlist["id"], items=track_ids)

    return playlist
