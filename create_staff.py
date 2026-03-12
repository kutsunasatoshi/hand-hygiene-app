import sqlite3

DB="database.db"

wards = [
"E01","E02","E03","E05","E06","E07","E08","E09","E10","E11","E12","E13",
"IVR","NICU","W05","W06","W08","W09","W10","W11","W12","W13",
"アイセンター","オンコロジーセンター","リハビリテーション部",
"外来","外来中央処置室","産科病棟","第1ICU","第2ICU","透析室"
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DELETE FROM staff")

ward_no=1

for ward in wards:

    for i in range(1,101):

        staff_id = f"{ward_no:02}{i:03}"

        cur.execute(
            "INSERT INTO staff VALUES(?,?,?)",
            (staff_id, ward, 1)
        )

    ward_no += 1

conn.commit()
conn.close()

print("staff 登録完了")
