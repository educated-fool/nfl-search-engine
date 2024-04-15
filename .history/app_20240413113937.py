from flask import Flask, request, render_template_string
from pymongo import MongoClient
import psycopg
import requests

# Constants and configurations
API_KEY = '2c96346235e54c7f9f7542fc3e69d6da'
MONGO_URI = 'localhost'
MONGO_PORT = 27017
PSQL_HOST = "localhost"
PSQL_DB = "my_database"
PSQL_USER = "postgres"
PSQL_PASS = ""
STATIC_URL_PATH = ''
STATIC_FOLDER = 'static'
APP_PORT = 5010

app = Flask(__name__, static_url_path=STATIC_URL_PATH, static_folder=STATIC_FOLDER)

# Database setup
client = MongoClient(MONGO_URI, MONGO_PORT)
db = client.nfl
players_collection = db.players
conn = psycopg.connect(
    host=PSQL_HOST,
    dbname=PSQL_DB,
    user=PSQL_USER,
    password=PSQL_PASS
)

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NFL Players Search Engine</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; }
        h1, h2, h3 { color: #333; }
        p, table { width: 80%; margin: auto; text-align: center; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
        table { border-collapse: collapse; margin-bottom: 20px; }
        .bold { font-weight: bold; }
        #fantasyPointsChart { width: 50%; height: 300px; margin: auto; }
        header img { width: 100px; position: absolute; top: 10px; left: 10px; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <img src="{{ url_for('static', filename='NFL-logo.png') }}" alt="NFL Logo">
    </header>
    <h1>NFL Players Search Engine</h1>
    <form method="post">
        Player Name: <input type="text" name="player_name">
        Season: <select name="season">
            <option value="2020">2020</option>
            <option value="2021">2021</option>
            <option value="2022">2022</option>
            <option value="2023">2023</option>
        </select>
        <input type="submit" value="Search">
    </form>
    {% if player_info %}
        <h2>{{ player_name }}</h2>
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
        <h3>Player Fantasy Stats</h3>
        <table>
            <tr>
                <th>Week</th>
                <th>Home/Away</th>
                <th>Opponent</th>
                <th class='bold'>FantasyPointsPPR</th>
                <th>Passing Yards</th>
                <th>Rushing Yards</th>
                <th>Receiving Yards</th>
                <th>Touchdowns</th>
                <th>Interceptions</th>
                <th>Fumbles</th>
                <th>Tackles</th>
                <th>Sacks</th>
            </tr>
            {% for stat in player_stats %}
            <tr>
                <td>{{ stat.Week }}</td>
                <td>{{ stat.HomeOrAway }}</td>
                <td>{{ stat.Opponent }}</td>
                <td class='bold'>{{ stat.FantasyPointsPPR }}</td>
                <td>{{ stat.PassingYards }}</td>
                <td>{{ stat.RushingYards }}</td>
                <td>{{ stat.ReceivingYards }}</td>
                <td>{{ stat.Touchdowns }}</td>
                <td>{{ stat.Interceptions }}</td>
                <td>{{ stat.Fumbles }}</td>
                <td>{{ stat.Tackles }}</td>
                <td>{{ stat.Sacks }}</td>
            </tr>
            {% endfor %}
        </table>
        <canvas id="fantasyPointsChart"></canvas>
        <script>
            var ctx = document.getElementById('fantasyPointsChart').getContext('2d');
            var fantasyPointsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: {{ weeks|tojson }},
                    datasets: [{
                        label: 'Fantasy Points PPR',
                        data: {{ fantasy_points_ppr|tojson }},
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    maintainAspectRatio: true
                }
            });
        </script>
    {% endif %}
    <h3>News Around the League</h3>
    {% for article in league_news %}
        <table>
            <tr>
                <td><a href="{{ article['Url'] }}">{{ article['Title'] }} ({{ article['TimeAgo'] }})</a></td>
                <td>{{ article['Content'] }}</td>
            </tr>
        </table>
    {% endfor %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def search():
    league_news = []
    player_name = ''
    player_info = {}
    player_stats = []
    weeks = []
    fantasy_points_ppr = []

    if request.method == 'POST':
        player_name = request.form['player_name']
        selected_season = request.form['season']
        regex = {'$regex': '^{}$'.format(player_name), '$options': 'i'}  # Case insensitive search
        player = players_collection.find_one({"Name": regex})
        if player:
            player_id = player['PlayerID']
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
            # Fetch player stats from PostgreSQL using Season
            with conn.cursor() as cur:
                query = """
                    SELECT Week, HomeOrAway, Opponent, FantasyPointsPPR, PassingYards, 
                           RushingYards, ReceivingYards, Touchdowns, Interceptions, Fumbles, 
                           Tackles, Sacks 
                    FROM player_game_stats 
                    WHERE PlayerID = %s AND Season = %s 
                    ORDER BY Week
                """
                cur.execute(query, (player_id, selected_season))
                rows = cur.fetchall()
                for row in rows:
                    weeks.append(row[0])
                    fantasy_points_ppr.append(row[3])
                    player_stats.append({
                        'Week': row[0],
                        'HomeOrAway': row[1],
                        'Opponent': row[2],
                        'FantasyPointsPPR': row[3],
                        'PassingYards': row[4],
                        'RushingYards': row[5],
                        'ReceivingYards': row[6],
                        'Touchdowns': row[7],
                        'Interceptions': row[8],
                        'Fumbles': row[9],
                        'Tackles': row[10],
                        'Sacks': row[11]
                    })

    # Fetch league news
    league_url = f"https://api.sportsdata.io/v3/nfl/scores/json/News?key={API_KEY}"
    league_response = requests.get(league_url)
    if league_response.status_code == 200:
        league_news = league_response.json()[:5]  # Get the top 5 news items for the league

    return render_template_string(
        HTML_TEMPLATE, 
        league_news=league_news, 
        player_name=player_name, 
        player_info=player_info, 
        player_stats=player_stats, 
        weeks=weeks, 
        fantasy_points_ppr=fantasy_points_ppr
    )

if __name__ == '__main__':
    app.run(debug=True, port=5010)