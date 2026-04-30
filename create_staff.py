import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "database.db")))

WARDS = [
    "E01", "E02", "E03", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13",
    "IVR", "NICU", "W05", "W06", "W08", "W09", "W10", "W11", "W12", "W13",
    "アイセンター", "オンコロジーセンター", "リハビリテーション部",
    "外来", "外来中央処置室", "産科病棟", "第1ICU", "第2ICU", "透析室",
]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staff(
            id TEXT PRIMARY KEY,
            ward TEXT
        )
        """
    )
    cur.execute("DELETE FROM staff")

    ward_no = 1
    total = 0

    for ward in WARDS:
        for i in range(1, 101):
            staff_id = f"{ward_no:02}{i:03}"
            cur.execute(
                "INSERT INTO staff(id, ward) VALUES(?, ?)",
                (staff_id, ward),
            )
            total += 1
        ward_no += 1

    conn.commit()
    conn.close()

    print(f"staff 登録完了: {total} 件 -> {DB_PATH}")


if __name__ == "__main__":
    main()
