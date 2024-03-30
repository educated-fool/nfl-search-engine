from flask import Flask, request, render_template_string
from pymongo import MongoClient
import requests

app = Flask(__name__)

# MongoDB setup
client = MongoClient('localhost', 27017)
db = client.nfl
players_collection = db.players

# HTML template with a search bar and a placeholder to display news
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NFL Player News Search</title>
</head>
<body>
    <h1>Search for NFL Player News</h1>
    <form method="post">
        Player Name: <input type="text" name="player_name">
        <input type="submit" value="Search">
    </form>
    {% if news %}
        <h2>News for {{ player_name }}:</h2>
        {% for article in news %}
            <h3>{{ article['Title'] }}</h3>
            <p>{{ article['Content'] }}</p>
        {% endfor %}
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def search():
    news = []
    player_name = ''
    if request.method == 'POST':
        player_name = request.form.get('player_name')
        player = players_collection.find_one({"Name": player_name}, {"PlayerID": 1, "_id": 0})
        if player:
            player_id = player['PlayerID']
            # Fetch news by player ID
            api_key = '2c96346235e54c7f9f7542fc3e69d6da'
            url = f"https://api.sportsdata.io/v3/nfl/scores/json/NewsByPlayerID/{player_id}?key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                news = response.json()
    
    return render_template_string(HTML_TEMPLATE, news=news, player_name=player_name)

if __name__ == '__main__':
    app.run(debug=True, port=5010)