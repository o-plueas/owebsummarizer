from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def scrape_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        jina_url = f"https://r.jina.ai/{url}"

        response = requests.get(jina_url, headers=headers, timeout=10)
        

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Limit to 6000 chars to stay within token limits
        return text[:6000]
    except Exception as e:
        return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Please provide a URL."})

    if not url.startswith("http"):
        url = "https://" + url

    content = scrape_url(url)

    if not content:
        return jsonify({"error": "Could not fetch content from that URL. Try another."})

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert summarizer. When given webpage content:
1. Write a clear, concise summary in 2 sentences
2. List 2 key points as bullet points
3. Give a one-line conclusion

Format your response exactly like this:
**Summary**
[your summary here]

**Key Points**
- [point 1]
- [point 2]


**Conclusion**
[one line conclusion]"""
                },
                {
                    "role": "user",
                    "content": f"Summarize this webpage content:\n\n{content}"
                }
            ],
            max_tokens=100
        )
        summary = response.choices[0].message.content
        return jsonify({"summary": summary, "url": url})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)



