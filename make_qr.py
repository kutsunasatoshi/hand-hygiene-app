import qrcode

ids = [
"10001",
"10002",
"10003"
]

for staff_id in ids:

    url = f"http://127.0.0.1:5000/input/{staff_id}"

    img = qrcode.make(url)

    img.save(f"qr_{staff_id}.png")
