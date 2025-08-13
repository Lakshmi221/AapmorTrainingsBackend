import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger("openai_parser")

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables.")
    raise RuntimeError("Missing OPENAI_API_KEY")

# Initialize OpenAI client (defaults to api.openai.com)
client = OpenAI(api_key=api_key)

logger.info("Loaded environment variables.")
logger.info(f"Using OPENAI_API_KEY: {api_key[:6]}...")

# Check models available 
# try:
#     models = client.models.list()
#     print("✅ OpenAI key is valid. Models available:", [m.id for m in models.data])
# except Exception as e:
#     print("❌ Failed to validate OpenAI key. Error:", str(e))

prompt = """
You will receive content from a PowerPoint presentation, organized by slides.

Your task is to classify this content into a **flat JSON array** of structured objects. Each object must follow one of the schemas below.

---

1. Title Block (Slide 1 only):
{
  "type": "title",
  "slide_number": 1,
  "title": "Title of the presentation"
}

---

2. Content Block:
{
  "type": "content",
  "slide_number": 2,
  "heading": "Main heading",  
  "subheadings": [
    {
      "subheading": "Subheading",
      "content": ["point 1", "point 2"],
      "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    }
  ]
}

---

3. Question Block:
{
  "type": "question",
  "slide_number": 3,
  "question": "Your question?",
  "options": ["Option A", "Option B", "Option C"],
  "answers": ["Option B"],     // must match one of the options exactly
  "question_type": "single"    // or "multiple"
}

---

Rules:
- You must return a **raw JSON array only**. No markdown, no explanations, no formatting.
- Slide 1 must return a single object of type `"title"` with a `"title"` field. If no clear title is found, generate one from the content.
- Use `"Untitled"` for missing headings or subheadings.
- If a slide has both content and questions, split them into separate JSON objects.
- If a correct answer is given using a letter (e.g., "Correct Answer: C"), convert it into the **actual string** from the `options` array by matching its position.
- Strip any letter prefixes like `"A. "`, `"B. "`, etc., from all options. Only include the **cleaned option text** in the `options` array.
- The `answers` field must always contain only the **cleaned option strings**, exactly matching one or more of the `options`.
- Never return letter answers like `"C"` or `"B. Something"`. Only use clean strings from the `options`.
- Use `"question_type": "multiple"` only if the question explicitly says "select all that apply" or similar.
- Every object must include a valid `slide_number` field.


---

Slides:

"""


def classify_ppt(slides):
    logger.info("Preparing slide content for classification...")
    slide_text = ""
    for slide in slides:
        slide_text += f"\nSlide {slide['slide_number']}:\n"
        for line in slide['content']:
            slide_text += f"- {line.strip()}\n"
        if 'images' in slide and slide['images']:
            slide_text += "\nImages:\n"
            for img_url in slide['images']:
                slide_text += f"- [Image] {img_url}\n"

    try:
        logger.info("Sending slide content to OpenAI for classification...")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert in classifying presentation content into JSON structure."},
                {"role": "user", "content": prompt + slide_text}
            ],
            model="gpt-4o",
        )
        logger.info("Received classification response from OpenAI.")
        return response.choices[0].message.content
    except Exception as e:
        logger.exception("Error during classification request")
        return None