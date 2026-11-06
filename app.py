from flask import Flask, jsonify, render_template
import sqlite3

app = Flask(__name__)
DB_NAME = "recipes.db"  # Or whatever your database name is


def get_db_connection():
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/recipes")
def get_recipes():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM recipes")
  rows = cursor.fetchall()
  conn.close()
  return jsonify([dict(row) for row in rows])


@app.route("/api/recipes/random5")
def get_random_five():
  conn = get_db_connection()
  cursor = conn.cursor()
  # Randomly fetch 5 recipes from your recipes table
  cursor.execute("SELECT * FROM recipes ORDER BY RANDOM() LIMIT 6")
  rows = cursor.fetchall()
  conn.close()
  return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
  app.run(debug=True, port=5000)