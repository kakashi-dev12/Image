import os
import uuid
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from rembg import remove
import shutil

# ✅ No need to load .env
# from dotenv import load_dotenv
# load_dotenv()

# 🔐 Getting environment variables directly (Render-style)
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
STABILITY_API_KEY = os.environ["STABILITY_API_KEY"]

# ✅ Pyrogram bot initialization
app = Client("ai_image_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🧠 Dictionary to store last image path per user
user_memory = {}
def generate_image(prompt):
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "steps": 30,
        "width": 512,
        "height": 512,
        "seed": 0,
        "cfg_scale": 7,
        "samples": 1,
        "text_prompts": [{"text": prompt, "weight": 1}]
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        output = response.json()["artifacts"][0]["base64"]
        image_path = f"generated/{uuid.uuid4()}.png"
        os.makedirs("generated", exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(requests.get("data:image/png;base64," + output).content)
        return image_path
    else:
        return None
def overlay_text(image_path, text):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((10, 10), text, font=font, fill="white")
    img.save(image_path)
    return image_path
def replace_background(img_path):
    input_img = Image.open(img_path)
    output = remove(input_img)
    bg_img = Image.new("RGBA", output.size, (255, 255, 255, 255))
    bg_img.paste(output, (0, 0), output)
    output_path = f"edited/{uuid.uuid4()}.png"
    os.makedirs("edited", exist_ok=True)
    bg_img.save(output_path)
    return output_path
@app.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply(
        "👋 **Welcome to AI Image Bot!**\n"
        "Type /help to see how to create and edit images."
    )


@app.on_message(filters.command("help"))
async def help_command(_, m: Message):
    await m.reply(
        "**🧠 AI Image Bot Commands:**\n\n"
        "`/generate <prompt>` – Create a new AI image\n"
        "`/text <your text>` – Add text on your last image\n"
        "Reply to an image + `/edit bg` – Remove/change background\n"
        "`/gibli` – Make Ghibli-style anime portrait\n"
        "`/replace` – Replace face in generated image with yours"
    )
@app.on_message(filters.command("generate"))
async def generate(_, m: Message):
    prompt = " ".join(m.command[1:])
    if not prompt:
        return await m.reply("❌ Please include a prompt, e.g. `/generate futuristic robot`.")
    
    waiting = await m.reply("🎨 Generating image, please wait...")
    image_path = generate_image(prompt)

    if image_path:
        user_memory[m.from_user.id] = image_path
        await waiting.delete()
        await m.reply_photo(image_path, caption="✅ Generated!")
    else:
        await waiting.edit("❌ Failed to generate image. Try again.")
@app.on_message(filters.command("text"))
async def add_text(_, m: Message):
    uid = m.from_user.id
    if uid not in user_memory:
        return await m.reply("❌ No image found. First use `/generate`.")

    text = " ".join(m.command[1:])
    if not text:
        return await m.reply("❌ Please provide text, e.g. `/text Hello World`.")

    path = overlay_text(user_memory[uid], text)
    await m.reply_photo(path, caption="📝 Text added.")
@app.on_message(filters.command("edit") & filters.reply)
async def edit_image(_, m: Message):
    if "bg" in m.text:
        replied = m.reply_to_message
        if replied.photo:
            file_path = await replied.download()
            path = replace_background(file_path)
            await m.reply_photo(path, caption="✅ Background edited.")
        else:
            await m.reply("❌ Please reply to an image to edit.")
    else:
        await m.reply("❓ Unknown edit type. Try `/edit bg`.")
@app.on_message(filters.command("gibli") & filters.reply)
async def gibli_image(_, m: Message):
    replied = m.reply_to_message
    if not replied.photo:
        return await m.reply("❌ Please reply to a clear photo of your face.")

    msg = await m.reply("✨ Creating Ghibli-style portrait...")

    file_path = await replied.download()
    gibli_prompt = f"Ghibli anime style portrait of a person"

    user_memory[m.from_user.id] = file_path
    image_path = generate_image(gibli_prompt)

    if image_path:
        await msg.delete()
        await m.reply_photo(image_path, caption="🌸 Ghibli Style Ready!")
    else:
        await msg.edit("❌ Failed to apply Ghibli style.")
@app.on_message(filters.command("replace") & filters.reply)
async def face_swap(_, m: Message):
    try:
        import face_recognition
    except:
        return await m.reply("❌ Face swapping requires `face_recognition`. Please install it.")

    uid = m.from_user.id
    if uid not in user_memory:
        return await m.reply("❌ No generated image found. Use `/generate` first.")

    replied = m.reply_to_message
    if not replied.photo:
        return await m.reply("❌ Please reply to a clear photo of your face.")

    original_img = face_recognition.load_image_file(user_memory[uid])
    swap_img_path = await replied.download()
    swap_img = face_recognition.load_image_file(swap_img_path)

    face_locations = face_recognition.face_locations(swap_img)
    if not face_locations:
        return await m.reply("❌ No face detected in your photo.")

    # Simulate face swap by replacing image (real swap would need OpenCV/dlib)
    shutil.copyfile(swap_img_path, user_memory[uid])
    await m.reply_photo(swap_img_path, caption="🧑‍🎤 Face replaced (simulated).")

# Run the bot
app.run()
