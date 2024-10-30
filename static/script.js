"use strict";

const MAX_CHARS = 150;
const MAX_TRACK_COUNT = 100;
const MIN_TRACK_COUNT = 1;

main();

// Initialize event listeners if buttons are not NULL.
function main() {
  const loginButton = document.getElementById("login-button");
  const generateButton = document.getElementById("generate-button");
  const backButton = document.getElementById("back-button");
  const userInput = document.getElementById("user-input");
  const charCountInput = document.getElementById("char-count");
  const trackCountInput = document.getElementById("track-count");

  // Event listener for login button
  if (loginButton) {
    loginButton.addEventListener("click", login);
  }

  // Event listeners for the main page
  if (userInput && charCountInput && trackCountInput && generateButton) {
    // Checks if both user input and track count are non empty.
    function toggleGenerateButton() {
      if (userInput.value.trim() !== "" && trackCountInput.value.trim() !== "") {
        generateButton.disabled = false;
      } else {
        generateButton.disabled = true;
      }
    }

    // Event listener for user input
    userInput.addEventListener("input", () => {
      // Enable or disable based on user input and track count
      toggleGenerateButton();

      // Update character count
      let charCount = userInput.value.length;
      charCountInput.textContent = `${charCount} / ${MAX_CHARS}`;
    });

    // Event listener for track count input
    trackCountInput.addEventListener("input", () => {
      // Enable or disable based on user input and track count
      toggleGenerateButton();

      // Ensure track count does not exceed MAX_TRACK_COUNT
      if (trackCountInput.value > MAX_TRACK_COUNT) {
        trackCountInput.value = MAX_TRACK_COUNT;
        alert(`The maximum number of tracks is ${MAX_TRACK_COUNT}.`);
      }

      // Ensure track count does not fall below MIN_TRACK_COUNT, unless empty
      if (trackCountInput.value < MIN_TRACK_COUNT && trackCountInput.value !== "") {
        trackCountInput.value = MIN_TRACK_COUNT;
        alert(`The minimum number of tracks is ${MIN_TRACK_COUNT}`);
      }
    });

    // Event listener for generate playlist button
    generateButton.addEventListener("click", generatePlaylist);
  }

  // Event listener for back button
  if (backButton) {
    backButton.addEventListener("click", index);
  }
}

// Redirect to the index endpoint.
function index() {
  window.location.href = urls.index;
}

// Redirect to the login endpoint.
function login() {
  window.location.href = urls.login;
}

// Generates a playlist based on user input.
// Sends a POST request to the generate_playlist endpoint and processes the user input.
// If successful, enables a button to view the generated playlist.
async function generatePlaylist() {
  // Disable generate button view playlist button
  const viewButton = document.getElementById("view-button");
  const generateButton = document.getElementById("generate-button");
  viewButton.disabled = true;
  generateButton.disabled = true;

  // Retrieve user input and track count from input field
  const userInput = document.getElementById("user-input").value;
  const trackCount = parseInt(document.getElementById("track-count").value);

  // Send a POST request to the server with user input
  let response = await fetch(urls.generatePlaylist, {
    method: "POST",
    headers: { "Content-Type": "application/json" }, // Set content type to JSON
    body: JSON.stringify({ userInput: userInput, trackCount: trackCount }),
    credentials: "include", // Include cookies with the request
  });

  // Parse the JSON response from the server
  let data = await response.json();
  generateButton.disabled = false;  // Enable generate button

  // Check for HTTP status code
  if (!response.ok) {
    if (data.error === "user_not_authenticated" || response.status == 401) {
      alert("Your session has expired. Redirecting you to the login page...");
      index(); // Redirect user to the login page
    } else {
      alert("An unexpected error occured. Please try again.");
    }
    return;
  }

  // If the resposne contains a valid playlist URL, enable the view playlist button
  if (data.playlist_url) {
    viewButton.disabled = false; // Enable view playlist button

    // Open playlist url in a new tab
    viewButton.addEventListener("click", () => {
      window.open(data.playlist_url, "_blank");
    });
  }
}
