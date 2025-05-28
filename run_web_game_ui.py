# run_web_game_ui.py
from flask import Flask, request, redirect, render_template_string
from game_constants import *
from game_status_checks import *
from player_survey import run_survey_about_llm_player
from pathlib import Path
import random

app = Flask(__name__)
game_dir = None
name = None
is_mafia = None
voted_out = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="2">
    <title>Mafia Game</title>
</head>
<body style="font-family: monospace; white-space: pre-wrap;">
    <h2>Live Game Chat</h2>
    <div style="border:1px solid #ccc; padding:10px; background-color:#f8f8f8;">
        {% for line in chat_lines %}
            <div style="color:{{ line.color }}">{{ line.text }}</div>
        {% endfor %}
    </div>

    {% if show_input %}
    <h3>Send a Message</h3>
    <form method="POST" action="/send">
        <input type="text" name="msg" style="width: 80%;" autofocus>
        <input type="submit" value="Send">
    </form>
    {% endif %}

    {% if show_vote %}
    <h3>Vote to Eliminate</h3>
    <form method="POST" action="/vote">
        <select name="vote_for">
            {% for p in vote_options %}
                <option value="{{ p }}">{{ p }}</option>
            {% endfor %}
        </select>
        <input type="submit" value="Vote">
    </form>
    {% endif %}

    {% if show_survey %}
    <h3>Survey</h3>
    <form method="POST" action="/survey">
        <textarea name="feedback" rows="4" cols="60"></textarea><br>
        <input type="submit" value="Submit Survey">
    </form>
    {% endif %}
</body>
</html>
"""

def get_chat_lines():
    lines = []
    def add_lines(file, color):
        if (game_dir / file).exists():
            for line in (game_dir / file).read_text().splitlines():
                lines.append({"text": line, "color": color})
    add_lines(PUBLIC_MANAGER_CHAT_FILE, "blue")
    add_lines(PUBLIC_DAYTIME_CHAT_FILE, "black")
    if is_mafia:
        add_lines(PUBLIC_NIGHTTIME_CHAT_FILE, "purple")
    return lines

@app.route("/", methods=["GET"])
def index():
    global voted_out
    chat_lines = get_chat_lines()

    show_input = not is_voted_out(name, game_dir) and (is_mafia or not is_nighttime(game_dir)) and not is_time_to_vote(game_dir)
    show_vote = is_time_to_vote(game_dir) and not is_voted_out(name, game_dir)
    show_survey = is_game_over(game_dir) and not voted_out

    vote_options = []
    if show_vote:
        vote_options = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
        if name in vote_options:
            vote_options.remove(name)

    return render_template_string(HTML_TEMPLATE,
                                  chat_lines=chat_lines,
                                  show_input=show_input,
                                  show_vote=show_vote,
                                  show_survey=show_survey,
                                  vote_options=vote_options)

@app.route("/send", methods=["POST"])
def send():
    msg = request.form["msg"].strip()
    if msg:
        with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
            f.write(format_message(name, msg))
    return redirect("/")

@app.route("/vote", methods=["POST"])
def vote():
    vote_for = request.form["vote_for"]
    with open(game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name), "a") as f:
        f.write(vote_for + "\n")
    return redirect("/")

@app.route("/survey", methods=["POST"])
def survey():
    feedback = request.form["feedback"]
    # Save or process feedback using your existing survey function
    run_survey_about_llm_player(game_dir, name)  # customize if needed
    global voted_out
    voted_out = True
    return redirect("/")

def initialize():
    global game_dir, name, is_mafia
    game_dir = get_game_dir_from_argv()
    player_names = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    random.shuffle(player_names)
    name = get_player_name_from_user(player_names, GET_CODE_NAME_FROM_USER_MESSAGE)
    is_mafia = get_is_mafia(name, game_dir)
    (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).write_text(JOINED)
    while not all_players_joined(game_dir):
        pass
    print(f"Welcome {name}! Open http://localhost:8888 in your browser.")

if __name__ == '__main__':
    initialize()
    app.run(host="0.0.0.0", port=8000)
