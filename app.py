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
            # Geocode the location to get latitude and longitude
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geocode_params = {
                'address': location,
                'key': GOOGLE_PLACES_API_KEY
            }
            geocode_response = requests.get(geocode_url, params=geocode_params)
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()

            if geocode_data['status'] != 'OK':
                flash('Geocoding failed. Please check the location and try again.', 'danger')
                return redirect(url_for('find'))

            location_coords = geocode_data['results'][0]['geometry']['location']
            lat, lng = location_coords['lat'], location_coords['lng']

            # Use Places API to find specialists
            places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            places_params = {
                'location': f"{lat},{lng}",
                'radius': 50000,  # 50 km radius, adjust as needed
                'keyword': query,
                'key': GOOGLE_PLACES_API_KEY
            }
            places_response = requests.get(places_url, params=places_params)
            places_response.raise_for_status()
            places_data = places_response.json()

            if places_data['status'] != 'OK':
                flash('Could not retrieve specialist information from Google Places. Please try again.', 'danger')
                return redirect(url_for('find'))

            experts_data = []
            for place in places_data.get('results', [])[:20]:  # Fetch up to 20 places
                expert = {
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'rating': place.get('rating', 'N/A'),
                    'place_id': place.get('place_id'),
                    'types': place.get('types', [])
                }
                experts_data.append(expert)

            if not experts_data:
                flash('No specialists found for the given criteria.', 'danger')
                return redirect(url_for('find'))

            # Craft the prompt for ChatGPT
            prompt = (
                f"Based on the following data, provide a list of the top 5 {query} specialists near {location}. "
                f"For each specialist, include their name, address, rating, and types.\n\nData:\n"
            )
            for expert in experts_data:
                prompt += (
                    f"Name: {expert['name']}\n"
                    f"Address: {expert['address']}\n"
                    f"Rating: {expert['rating']}\n"
                    f"Types: {', '.join(expert['types'])}\n\n"
                )
            prompt += (
                "Return the response in JSON format with the following structure:\n"
                "[{'name': 'Specialist Name', 'address': 'Address', 'rating': 'Rating', 'types': 'Types'}]"
            )

            # Make a call to OpenAI's API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=700
            )

            # Extract the assistant's reply
            expert_list_raw = response.choices[0].message['content']
            flash('Expert list retrieved successfully!', 'success')

            # Attempt to parse JSON from the response
            try:
                start = expert_list_raw.find('[')
                end = expert_list_raw.rfind(']') + 1
                json_str = expert_list_raw[start:end]
                experts = json.loads(json_str.replace("'", '"'))
            except (json.JSONDecodeError, ValueError) as error:
                flash(f"Error parsing response: {error}", 'danger')
                experts = []

            if not experts:
                flash('Could not interpret data. Please try again.', 'danger')

            return render_template(
                'find.html',
                experts=experts,
                query=query,
                location=location,
                google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY')
            )

        except requests.RequestException as e:
            flash(f"An error occurred while fetching data: {str(e)}", 'danger')
            return redirect(url_for('find'))

    return render_template('find.html', google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
