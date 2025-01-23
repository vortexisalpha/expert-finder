import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import openai
from dotenv import load_dotenv
import json
import requests
import urllib.parse

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure randomly generated key

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set your Google Places API key
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        return redirect(url_for('profile'))
    return render_template('signin.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        location = request.form.get('location')

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
            prompt = (
                f"Provide a list of the top 5 {query} in {location}. "
                f"For each expert, include their name, a brief description, and location."
                f"Return the response in JSON format with the following structure:\n"
                f"[{{'name': 'Expert Name', 'description': 'Brief description', 'location': 'Location'}}]"
            )

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )

            expert_list_raw = response.choices[0].message['content']

            try:
                start = expert_list_raw.find('[')
                end = expert_list_raw.rfind(']') + 1
                json_str = expert_list_raw[start:end]
                experts = json.loads(json_str.replace("'", '"'))
            except (json.JSONDecodeError, ValueError):
                experts = []

            if not experts:
                flash('Could not retrieve expert information. Please try again.', 'danger')

            return render_template('find.html', experts=experts, query=query, location=location,
                                   google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('find'))

    return render_template('find.html', google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
