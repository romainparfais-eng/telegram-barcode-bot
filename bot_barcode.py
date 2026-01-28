import os, io, zipfile, random, string, re, tempfile
from pathlib import Path
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes
from barcode import get as barcode_get
from barcode.writer import ImageWriter

ALPHABET = string.ascii_uppercase + string.digits
FORMAT = re.compile(r"^[A-Z0-9]{4} [A-Z0-9]{4}$")

OPTIONS = {
    "module_width": 0.25,
    "module_height": 15,
    "quiet_zone": 6.5,
    "font_size": 12,
    "text_distance": 4,
    "write_text": True,
    "background": "white",
    "foreground": "black",
    "dpi": 300,
}

def random_code():
    return "".join(random.choice(ALPHABET) for _ in range(4)) + " " + \
           "".join(random.choice(ALPHABET) for _ in range(4))

def barcode_png(code):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "code"
        barcode_get("code128", code, writer=ImageWriter()).save(str(p), options=OPTIONS)
        return Path(str(p) + ".png").read_bytes()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 Bot Code-barres\n\n"
        "/one → 1 code\n"
        "/zip 100 → ZIP de 100 images\n"
        "/from XXXX XXXX → code personnalisé"
    )

async def one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = random_code()
    img = barcode_png(code)
    await update.message.reply_photo(photo=io.BytesIO(img), caption=code)

async def from_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = " ".join(context.args).upper()
    if not FORMAT.match(code):
        await update.message.reply_text("Format invalide (XXXX XXXX)")
        return
    img = barcode_png(code)
    await update.message.reply_photo(photo=io.BytesIO(img), caption=code)

async def zip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = int(context.args[0])
    zipbuf = io.BytesIO()
    with zipfile.ZipFile(zipbuf, "w") as z:
        for i in range(n):
            code = random_code()
            z.writestr(f"codes_mcd/{i+1:04d}.png", barcode_png(code))
    zipbuf.seek(0)
    await update.message.reply_document(zipbuf, filename="codes_barres.zip")

def main():
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("one", one))
    app.add_handler(CommandHandler("from", from_code))
    app.add_handler(CommandHandler("zip", zip_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
