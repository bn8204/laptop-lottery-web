
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import random, csv, pandas as pd
from datetime import datetime
import logging
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "your-secret-key"
logging.basicConfig(filename="lottery.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def read_list_from_file(file_stream):
    return [line.decode('utf-8').strip() for line in file_stream if line.strip()]

def run_lottery(laptops, users):
    if len(laptops) > len(users):
        raise ValueError("More laptops than users.")
    winners = random.sample(users, len(laptops))
    random.shuffle(laptops)
    return list(zip(laptops, winners))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        laptops_file = request.files.get("laptops")
        users_file = request.files.get("users")
        if not laptops_file or not users_file:
            flash("Please upload both files.")
            return redirect(url_for("index"))
        laptops = read_list_from_file(laptops_file.stream)
        users = read_list_from_file(users_file.stream)
        try:
            winners = run_lottery(laptops, users)
        except Exception as e:
            flash(str(e))
            return redirect(url_for("index"))

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.DataFrame(winners, columns=["Laptop Serial", "Username"])
        df.to_csv(f"results_{ts}.csv", index=False)
        df.to_excel(f"results_{ts}.xlsx", index=False, engine='openpyxl')

        logging.info(f"Lottery run at {ts}, {len(winners)} winners")
        return render_template("index.html", winners=winners, ts=ts)

    return render_template("index.html", winners=None)

@app.route("/download/<filetype>/<ts>")
def download(filetype, ts):
    filename = f"results_{ts}.{ 'csv' if filetype=='csv' else 'xlsx' }"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    flash("File not found.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
