# Expert Finder

## Installing Dependencies
Create a requirements.txt file to manage your project dependencies.

```plaintext
Flask==2.3.2
python-dotenv==1.0.0
openai==0.27.0
```

Install the dependencies:

```sh
pip install -r requirements.txt
```

## Creating the Flask Application
app.py
This is the main Flask application file.

```python
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import openai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure randomly generated key

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Since authentication isn't required, we'll just redirect to profile
        # You can add form validation or session handling here if needed
        return redirect(url_for('profile'))
    return render_template('signin.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # Capture profile details
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        location = request.form.get('location')

        # Store details in session
        session['first_name'] = first_name
        session['last_name'] = last_name
        session['email'] = email
        session['location'] = location

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

@app.route('/find', methods=['GET', 'POST'])
def find():
    if request.method == 'POST':
        query = request.form.get('query')
        location = request.form.get('location')

        if not query or not location:
            flash('Please provide both the expertise and select your location.', 'danger')
            return redirect(url_for('find'))

        try:
            # Craft the prompt for ChatGPT
            prompt = (
                f"Provide a list of the top 5 {query} in {location}. "
                f"For each expert, include their name, a brief description, and location."
                f"Return the response in JSON format with the following structure:\n"
                f"[{{'name': 'Expert Name', 'description': 'Brief description', 'location': 'Location'}}]"
            )

            # Make a call to OpenAI's API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )

            # Extract the assistant's reply
            expert_list_raw = response.choices[0].message['content']

            # Attempt to parse JSON from the response
            try:
                # Extract JSON part from the response
                start = expert_list_raw.find('[')
                end = expert_list_raw.rfind(']') + 1
                json_str = expert_list_raw[start:end]
                experts = json.loads(json_str.replace("'", '"'))  # Replace single quotes for JSON compliance
            except (json.JSONDecodeError, ValueError):
                experts = []  # Fallback in case of parsing issues

            if not experts:
                flash('Could not retrieve expert information. Please try again.', 'danger')

            return render_template('find.html', experts=experts, query=query, location=location,
                                   google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('find'))

    return render_template('find.html', google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

if __name__ == '__main__':
    app.run(debug=True)
```

## Templates
All HTML templates are stored in the templates/ directory.

### base.html
A base template that includes the navbar and common structures.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Expert Finder</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <!-- Font Awesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
    {% block head %}{% endblock %}
</head>
<body>
    <!-- Navbar -->
    <nav>
        <div class="nav-container">
            <a href="{{ url_for('home') }}" class="logo">ExpertFinder</a>
            <ul class="nav-links">
                <li><a href="{{ url_for('home') }}"><i class="fas fa-home"></i> Home</a></li>
                <li><a href="{{ url_for('find') }}"><i class="fas fa-search"></i> Find</a></li>
                <li><a href="{{ url_for('profile') }}"><i class="fas fa-user"></i> Profile</a></li>
                <li><a href="{{ url_for('signin') }}"><i class="fas fa-sign-in-alt"></i> Sign In</a></li>
            </ul>
        </div>
    </nav>

    <!-- Flash Messages -->
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="flash {{ category }}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
    </div>

    <!-- Main Content -->
    <div class="container">
        {% block content %}{% endblock %}
    </div>

    {% block scripts %}{% endblock %}
</body>
</html>
```

### profile.html
Integrate Google Maps for location selection.

```html
{% extends 'base.html' %}

{% block head %}
    <!-- Google Maps JavaScript API -->
    <script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&callback=initMap" async defer></script>
{% endblock %}

{% block content %}
<div class="form-section">
    <h2>Your Profile</h2>
    <form method="POST" action="{{ url_for('profile') }}">
        <label for="first_name"><i class="fas fa-user"></i> First Name:</label>
        <input type="text" id="first_name" name="first_name" required value="{{ session.first_name if session.first_name }}">

        <label for="last_name"><i class="fas fa-user"></i> Last Name:</label>
        <input type="text" id="last_name" name="last_name" required value="{{ session.last_name if session.last_name }}">

        <label for="email"><i class="fas fa-envelope"></i> Email:</label>
        <input type="email" id="email" name="email" required value="{{ session.email if session.email }}">

        <label for="location"><i class="fas fa-map-marker-alt"></i> Location:</label>
        <input type="hidden" id="location" name="location" required value="{{ session.location if session.location }}">
        <div id="map"></div>

        <button type="submit" class="btn">Update Profile</button>
    </form>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/map.js') }}"></script>
<script>
    const initialLocation = "{{ session.location if session.location else 'New York, USA' }}";
</script>
{% endblock %}
```

### find.html
Enhance the layout with labeled text boxes and integrate Google Maps for location selection.

```html
{% extends 'base.html' %}

{% block head %}
    <!-- Google Maps JavaScript API -->
    <script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&callback=initFindMap" async defer></script>
{% endblock %}

{% block content %}
<div class="find-section">
    <h2>Find Experts</h2>
    <form method="POST" action="{{ url_for('find') }}">
        <div class="input-group">
            <label for="query">Find the best <i class="fas fa-search"></i></label>
            <input type="text" name="query" id="query" placeholder="e.g., Plumber, Electrician" required value="{{ request.form.query if request.form.query }}">
        </div>
        <div class="input-group">
            <label for="location"><i class="fas fa-map-marker-alt"></i> Your Location:</label>
            <input type="hidden" id="location" name="location" required value="{{ request.form.location if request.form.location }}">
            <div id="find-map"></div>
        </div>
        <button type="submit" class="btn">Find</button>
    </form>

    {% if experts %}
    <div class="results">
        <h3>Top 5 "{{ query }}" near "{{ location }}":</h3>
        <div class="expert-list">
            {% for expert in experts %}
                <div class="expert-card">
                    <h4>{{ expert.name }}</h4>
                    <p>{{ expert.description }}</p>
                    <p><strong>Location:</strong> {{ expert.location }}</p>
                </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/map.js') }}"></script>
<script>
    const initialFindLocation = "{{ location if location else 'New York, USA' }}";
</script>
{% endblock %}
```

### style.css
Enhance the CSS to style the Google Maps containers and expert result cards.

```css
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');

body {
    margin: 0;
    font-family: 'Roboto', sans-serif;
    background: linear-gradient(135deg, #ffe4e1 0%, #ffffff 100%); /* Light pink gradient */
    color: #333;
}

/* Navbar Styling */
nav {
    background: #ffb6c1; /* Light Pink */
    padding: 10px 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.8em;
    font-weight: bold;
    color: #ffffff;
    text-decoration: none;
}

.nav-links {
    list-style: none;
    display: flex;
    gap: 20px;
}

.nav-links li a {
    color: #ffffff;
    text-decoration: none;
    font-size: 1em;
    display: flex;
    align-items: center;
    gap: 5px;
}

.nav-links li a:hover {
    color: #333333;
}

/* Container */
.container {
    padding: 20px;
}

/* Home Section */
.home-section {
    text-align: center;
    padding: 100px 20px;
}

.home-section h1 {
    font-size: 3em;
    color: #d63384; /* Darker Pink */
}

.home-section p {
    font-size: 1.2em;
    margin: 20px 0;
}

.btn {
    background: #d63384; /* Darker Pink */
    color: #ffffff;
    padding: 12px 25px;
    border: none;
    border-radius: 25px;
    cursor: pointer;
    font-size: 1em;
    transition: background 0.3s ease, transform 0.2s ease;
    text-decoration: none;
}

.btn:hover {
    background: #c1207a;
    transform: scale(1.05);
}

/* Form Section */
.form-section {
    max-width: 600px;
    margin: 0 auto;
    background: #ffffff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.form-section h2 {
    text-align: center;
    color: #d63384;
    margin-bottom: 20px;
}

.form-section form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-section label {
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 5px;
}

.form-section input[type="text"],
.form-section input[type="email"],
.form-section input[type="password"] {
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 1em;
}

.form-section input[type="hidden"] {
    display: none;
}

/* Map Styling */
#map, #find-map {
    width: 100%;
    height: 300px;
    margin-top: 10px;
    border: 2px solid #d63384;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Find Section */
.find-section {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
}

.find-section h2 {
    color: #d63384;
    margin-bottom: 30px;
}

.find-section .input-group {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 25px;
}

.find-section .input-group label {
    margin-bottom: 8px;
    font-weight: bold;
}

.find-section .input-group input[type="text"] {
    width: 100%;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 25px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    font-size: 1em
