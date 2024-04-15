from flask import Flask, request, render_template_string
from pymongo import MongoClient
import requests

app = Flask(__name__)

# MongoDB setup
client = MongoClient('localhost', 27017)
db = client.nfl
players_collection = db.players

# Define API key globally
API_KEY = '2c96346235e54c7f9f7542fc3e69d6da'

# HTML template with a search bar, player info, player news, and league news
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NFL Players Search Engine</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; }
        h1 { color: #333; margin-bottom: 0; }
        h2 { color: #333; margin-top: 0; }
        p, table { width: 80%; margin: 10px auto; text-align: left; }
        input[type="text"] { width: 200px; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
        table { border-collapse: collapse; }
    </style>
</head>
<body>
    <h1>NFL Players Search Engine</h1>
    <form method="post">
        <input type="text" name="player_name" placeholder="Enter player name">
        <input type="submit" value="Search">
    </form>
    {% if player_name %}
        <h2>Results for "{{ player_name }}"</h2>
    {% endif %}
    {% if player_info %}
        <h3>Player Info</h3>
        <table>
            <tr>
                <th>Team</th>
                <th>Number</th>
                <th>Position</th>
                <th>Status</th>
                <th>Height</th>
                <th>Weight</th>
                <th>College</th>
                <th>Fantasy Position</th>
            </tr>
            <tr>
                <td>{{ player_info['Team'] }}</td>
                <td>{{ player_info['Number'] }}</td>
                <td>{{ player_info['Position'] }}</td>
                <td>{{ player_info['Status'] }}</td>
                <td>{{ player_info['Height'] }}</td>
                <td>{{ player_info['Weight'] }}</td>
                <td>{{ player_info['College'] }}</td>
                <td>{{ player_info['FantasyPosition'] }}</td>
            </tr>
        </table>
    {% endif %}
    {% if player_news %}
        <h3>News for "{{ player_name }}"</h3>
        {% for article in player_news %}
            <table>
                <tr>
                    <td><a href="{{ article['Url'] }}">{{ article['Title'] }} ({{ article['Author'] }})</a></td>
                    <td>{{ article['Content'] }}</td>
                </tr>
            </table>
        {% endfor %}
    {% endif %}
    <h3>News Around the League</h3>
    {% for article in league_news %}
        <table>
            <tr>
                <td><a href="{{ article['Url'] }}">{{ article['Title'] }} ({{ article['Author'] }})</a></td>
                <td>{{ article['Content'] }}</td>
            </tr>
        </table>
    {% endfor %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def search():
    player_news = []
    league_news = []
    player_name = ''
    player_info = {}

    if request.method == 'POST':
        player_name = request.form.get('player_name')
        player = players_collection.find_one({"Name": player_name})
        if player:
            player_id = player['PlayerID']
            # Fetch news by player ID
            url = f"https://api.sportsdata.io/v3/nfl/scores/json/NewsByPlayerID/{player_id}?key={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                player_news = response.json()[:1]  # Limit to the first news item for brevity
            # Populate player info
            player_info = {
                'Team': player.get('Team', ''),
                'Number': player.get('Number', ''),
                'Position': player.get('Position', ''),
                'Status': player.get('Status', ''),
                'Height': player.get('Height', ''),
                'Weight': player.get('Weight', ''),
                'College': player.get('College', ''),
                'FantasyPosition': player.get('FantasyPosition', '')
            }

    # Fetch league news
    league_url = f"https://api.sportsdata.io/v3/nfl/scores/json/News?key={API_KEY}"
    league_response = requests.get(league_url)
    if league_response.status_code == 200:
        league_news = league_response.json()[:5]  # Get the top 5 news items for the league

    return render_template_string(HTML_TEMPLATE, player_news=player_news, league_news=league_news, player_name=player_name, player_info=player_info)

if __name__ == '__main__':
    app.run(debug=True, port=5010)