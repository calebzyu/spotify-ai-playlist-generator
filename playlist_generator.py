from spotipy import Spotify
from openai import OpenAI
from pydantic import BaseModel

class PlaylistGenerator:
  """Responsible for generating a playlist. Calling PlaylistGenerator returns a playlist object."""

  def __init__(self, spotify: Spotify, user_input: str, track_count: int, api_key: str):
    """Initialize a playlist generator."""
    self.sp = spotify
    self.sp_id = self.sp.current_user()["id"]
    self.user_input = user_input
    self.track_count = track_count
    self.system_prompt = self.load_prompt("system-prompt.txt")
    self.client = OpenAI(api_key=api_key)

  def __call__(self):
    """Generate a Spotify playlist."""
    seeds = self.invoke_model_and_generate_seeds()
    # Set seeds[seed_type] to None if it's empty
    for seed_type in seeds:
      seeds[seed_type] = seeds[seed_type] if seeds[seed_type] else None
    # Generate playlist
    playlist = self.generate_playlist(
      seed_artists=seeds["artists"],
      seed_genres=seeds["genres"],
      seed_tracks=seeds["tracks"],
    )
    return playlist

  def load_prompt(self, filename: str) -> str:
    """Load a prompt from file."""
    with open(file=filename, mode="r", encoding="utf-8") as file:
      return file.read()

  def invoke_model_and_generate_seeds(self) -> dict[str, str]:
    """
    Invoke LLM model to generate JSON with the keys "artists", "genres", and "tracks". 
    Get seeds for each element in the model's response for the Spotify recommendations API.
    """
    completion = self.client.beta.chat.completions.parse(
      model="gpt-4o",
      messages=[
        {
          "role": "system",
          "content":
            self.system_prompt  # System prompt
        },
        {
          "role": "user",
          "content":
            self.user_input  # User input
        }
      ],
      response_format=ResponseFormat,
      temperature=1.25
    )
    print(completion.choices[0].message)  # Debug

    # Get parsed chat completion
    response = completion.choices[0].message.parsed
    print(response)  # Debug

    # Seeds to return
    seeds = {"artists": [], "genres": [], "tracks": []}

    # Validate genres
    if response.genres:
      # Get available Spotify genre seeds
      rec_genre_seeds = self.sp.recommendation_genre_seeds()["genres"]
      # Validates all genres generated by the model
      seeds["genres"] = [genre for genre in response.genres if genre in rec_genre_seeds]

    # Search for artists
    if response.artists:
      # Iterate over artist queries
      for query in response.artists:
        # Search Spotify by artist
        results = self.sp.search(q=query, type="artist", limit=10)
        # Get Spotify ID of the first result if results exist
        if results["artists"]["items"]:
          spotify_id = results["artists"]["items"][0]["id"]
          seeds["artists"].append(spotify_id)

    # Search for tracks
    if response.tracks:
      # Iterate over track queries
      for query in response.tracks:
        # Search Spotify by track
        results = self.sp.search(q=query, type="track", limit=10)
        # Get Spotify ID of the first result if results exist
        if results["tracks"]["items"]:
          spotify_id = results["tracks"]["items"][0]["id"]
          seeds["tracks"].append(spotify_id)

    return seeds

  def generate_playlist(
    self,
    seed_artists: list[str] = None,
    seed_genres: list[str] = None,
    seed_tracks: list[str] = None,
  ) -> dict:
    """Generate Spotify playlist object based on provided seeds."""

    print({"seed_artists": seed_artists, "seed_genres": seed_genres, "seed_tracks": seed_tracks})  # Debug

    # Fallback mechanism to enforce a single genre limit 
    if len(seed_genres) > 1:
      seed_genres = [seed_genres[0]]

    # Get Spotify recommendation results
    results = self.sp.recommendations(
      seed_artists=seed_artists,
      seed_genres=seed_genres,
      seed_tracks=seed_tracks,
      limit=self.track_count,  # Number of tracks as requested by the user
    )

    # Get track IDs for each track in results
    track_ids = [track["id"] for track in results["tracks"]]
    # Create new private playlist
    playlist = self.sp.user_playlist_create(user=self.sp_id, name="Generated Playlist", public=False)
    # Add tracks to playlist
    self.sp.playlist_add_items(playlist_id=playlist["id"], items=track_ids)

    return playlist

class ResponseFormat(BaseModel):
  """Reponse format for chat completion."""
  artists: list[str]
  tracks: list[str]
  genres: list[str]
