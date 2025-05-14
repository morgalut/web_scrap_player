import csv
import logging

def sanitize_url(url):
    try:
        url = str(url).strip().replace(";", "")
        return url if url.startswith("http") else None
    except:
        return None

def append_row_to_csv(path, row):
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

async def save_image(page, url, save_path):
    try:
        await page.goto(url, timeout=10000)
        image_data = await page.evaluate("""() => {
            return fetch(location.href)
                .then(res => res.arrayBuffer())
                .then(buf => Array.from(new Uint8Array(buf)));
        }""")
        with open(save_path, "wb") as f:
            f.write(bytearray(image_data))
    except Exception as e:
        logging.warning(f"⚠️ Image download failed from {url}: {e}")
