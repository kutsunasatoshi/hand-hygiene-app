from flask import Flask, request, render_template
import sqlite3
import datetime
import pandas as pd
import plotly.express as px
import calendar
import os
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "database.db"
RENDER_DISK_DB_PATH = Path("/var/data/database.db")
DB = Path(
    os.environ.get(
        "DB_PATH",
        str(RENDER_DISK_DB_PATH if Path("/var/data").exists() else DEFAULT_DB_PATH)
    )
)


def ensure_db_parent_dir():

    DB.parent.mkdir(parents=True, exist_ok=True)


def get_connection():

    ensure_db_parent_dir()

    conn = sqlite3.connect(str(DB), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")

    return conn


def table_has_column(conn, table_name, column_name):

    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")

    columns = [row[1] for row in cur.fetchall()]

    return column_name in columns


# -------------------------
# DB初期化
# -------------------------
def init_db():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS measurements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id TEXT,
        product TEXT,
        datetime TEXT,
        weight REAL,
        use_ml REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        name TEXT PRIMARY KEY,
        container_weight REAL,
        volume_ml REAL
    )
    """)

    # staffテーブル
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff(
        id TEXT PRIMARY KEY,
        ward TEXT
    )
    """)

    if not table_has_column(conn, "measurements", "product"):
        cur.execute("ALTER TABLE measurements ADD COLUMN product TEXT")

    if not table_has_column(conn, "staff", "ward"):
        cur.execute("ALTER TABLE staff ADD COLUMN ward TEXT")

    cur.execute("INSERT OR IGNORE INTO products VALUES('ノアテクトPRO',68,250)")
    cur.execute("INSERT OR IGNORE INTO products VALUES('Purell ADVANCEDフォーム',62,240)")
    cur.execute("INSERT OR IGNORE INTO products VALUES('サニサーラaqua light',47,250)")

    conn.commit()
    conn.close()


init_db()


@app.route("/healthz")
def healthz():

    return "ok", 200


# -------------------------
# 製剤一覧
# -------------------------
def get_products():

    conn = get_connection()

    df = pd.read_sql_query("SELECT name FROM products", conn)

    conn.close()

    return df["name"].tolist()


# -------------------------
# 容器重量
# -------------------------
def get_container_weight(product):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT container_weight
    FROM products
    WHERE name=?
    """, (product,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


# -------------------------
# 前回重量
# -------------------------
def get_previous_weight(staff_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT weight
    FROM measurements
    WHERE staff_id=?
    ORDER BY datetime DESC
    LIMIT 1
    """, (staff_id,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


def get_last_measurement(staff_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT product, weight
    FROM measurements
    WHERE staff_id=?
    ORDER BY datetime DESC
    LIMIT 1
    """, (staff_id,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0], row[1]

    return None, None


# -------------------------
# 測定保存
# -------------------------
def save_measurement(staff_id, product, weight):

    now = datetime.datetime.now()

    prev_weight = get_previous_weight(staff_id)
    container_weight = get_container_weight(product)

    use_ml = 0

    if prev_weight is not None and container_weight is not None:

        if weight > prev_weight:
            use_g = prev_weight - container_weight
        else:
            use_g = prev_weight - weight

        use_ml = use_g * 1.25

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO measurements(staff_id,product,datetime,weight,use_ml)
    VALUES(?,?,?,?,?)
    """, (staff_id, product, now, weight, use_ml))

    conn.commit()
    conn.close()


# -------------------------
# 入力ページ
# -------------------------
@app.route("/", methods=["GET","POST"])
def index():

    products = get_products()

    error = None

    if request.method == "POST":

        staff_id = request.form.get("staff_id","")
        product = request.form.get("product","")
        weight_str = request.form.get("weight","")

        if weight_str.strip() == "":
            error = "重量を入力してください"
        else:

            weight = float(weight_str)

            save_measurement(staff_id, product, weight)

    return render_template(
        "index.html",
        products=products,
        error=error
    )


# -------------------------
# QR入力
# -------------------------
@app.route("/input/<staff_id>", methods=["GET","POST"])
def input_staff(staff_id):

    products = get_products()
    last_product, last_weight = get_last_measurement(staff_id)

    error = None

    if request.method == "POST":

        product = request.form.get("product","")
        weight_str = request.form.get("weight","")

        if weight_str.strip() == "":
            error = "重量を入力してください"
        else:

            weight = float(weight_str)

            save_measurement(staff_id, product, weight)

    return render_template(
        "input.html",
        staff_id=staff_id,
        products=products,
        error=error,
        last_product=last_product,
        last_weight=last_weight
    )


# -------------------------
# 個人履歴
# -------------------------
@app.route("/staff/<staff_id>")
def staff_history(staff_id):

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT datetime,product,weight,use_ml
    FROM measurements
    WHERE staff_id=?
    ORDER BY datetime DESC
    """, conn, params=(staff_id,))

    conn.close()

    return render_template(
        "staff.html",
        staff_id=staff_id,
        data=df.to_dict("records")
    )


# -------------------------
# カレンダー
# -------------------------
@app.route("/calendar/<staff_id>")
def calendar_view(staff_id):

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT datetime,use_ml
    FROM measurements
    WHERE staff_id=?
    """, conn, params=(staff_id,))

    conn.close()

    if len(df) == 0:

        return render_template(
            "calendar_month.html",
            staff_id=staff_id,
            calendar_data=[]
        )

    df["date"] = pd.to_datetime(df["datetime"]).dt.date

    daily = df.groupby("date")["use_ml"].sum()

    today = datetime.date.today()

    cal = calendar.monthcalendar(today.year, today.month)

    calendar_data = []

    for week in cal:

        row = []

        for day in week:

            if day == 0:
                row.append({"day":"", "ml":""})
            else:

                d = datetime.date(today.year, today.month, day)

                ml = daily.get(d, 0)

                row.append({"day":day,"ml":ml})

        calendar_data.append(row)

    return render_template(
        "calendar_month.html",
        staff_id=staff_id,
        calendar_data=calendar_data
    )


# -------------------------
# 個人ランキング
# -------------------------
@app.route("/ranking")
def ranking():

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT staff_id,
           SUM(use_ml) as total_ml,
           COUNT(*) as n_records
    FROM measurements
    GROUP BY staff_id
    ORDER BY total_ml DESC
    LIMIT 10
    """, conn)

    conn.close()

    if len(df) == 0:
        return render_template(
            "ranking.html",
            graph_html="",
            table_data=[]
        )

    df["total_ml"] = df["total_ml"].fillna(0).round(1)
    df["rank"] = df.index + 1

    fig = px.bar(
        df,
        x="staff_id",
        y="total_ml",
        text="total_ml"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="使用量(ml)")

    return render_template(
        "ranking.html",
        graph_html=fig.to_html(full_html=False),
        table_data=df.to_dict("records")
    )


# -------------------------
# 病棟ランキング
# -------------------------
@app.route("/ward_ranking")
def ward_ranking():

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT staff.ward,SUM(measurements.use_ml) as total_ml
    FROM measurements
    JOIN staff
    ON measurements.staff_id=staff.id
    GROUP BY staff.ward
    ORDER BY total_ml DESC
    """, conn)

    conn.close()

    fig = px.bar(df, x="ward", y="total_ml")

    return render_template(
        "ward_ranking.html",
        graph_html=fig.to_html(full_html=False)
    )


# -------------------------
# ダッシュボード
# -------------------------
@app.route("/dashboard")
def dashboard():

    conn = get_connection()

    df = pd.read_sql_query("""
    SELECT staff.ward,SUM(measurements.use_ml) as total_ml
    FROM measurements
    JOIN staff
    ON measurements.staff_id=staff.id
    GROUP BY staff.ward
    """, conn)

    conn.close()

    fig = px.bar(df, x="ward", y="total_ml")

    return render_template(
        "dashboard.html",
        graph_html=fig.to_html(full_html=False)
    )

@app.route("/debug/ranking_data")
def debug_ranking_data():

    conn = sqlite3.connect(DB)

    df = pd.read_sql_query("""
    SELECT staff_id, SUM(use_ml) as total_ml, COUNT(*) as n_records
    FROM measurements
    GROUP BY staff_id
    ORDER BY total_ml DESC
    """, conn)

    conn.close()

    return df.to_html(index=False)

# -------------------------
# サーバ起動
# -------------------------
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )
