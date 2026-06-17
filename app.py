import streamlit as st
from groq import Groq
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Copy Transformer", page_icon="✨", layout="wide")

# ---------- API SETUP ----------
API_KEY = "use ur API_KEY"
client = Groq(api_key=API_KEY)

# ---------- TONE -> TEMPERATURE / TOP_P MAPPING ----------
TONE_SETTINGS = {
    "Professional": {"temperature": 0.3, "top_p": 0.7},
    "Casual": {"temperature": 0.6, "top_p": 0.85},
    "Witty": {"temperature": 0.9, "top_p": 0.95},
    "Persuasive": {"temperature": 0.7, "top_p": 0.9},
    "Inspirational": {"temperature": 0.8, "top_p": 0.92},
}

# ---------- PLATFORM RULES ----------
PLATFORM_RULES = {
    "LinkedIn": {
        "limit": 3000,
        "instructions": "Write a professional, well-structured LinkedIn post. Use line breaks between ideas. End with 3-4 relevant hashtags.",
    },
    "Instagram": {
        "limit": 2200,
        "instructions": "Write a punchy, engaging Instagram caption. Keep it short and visual. Include 5-8 relevant hashtags and 1-2 emojis.",
    },
    "Twitter/X": {
        "limit": 280,
        "instructions": "Write a concise, attention-grabbing tweet. Must fit within 280 characters including hashtags. Maximum 2 hashtags.",
    },
    "Email": {
        "limit": 5000,
        "instructions": "Write a formal marketing email with a subject line, greeting, body paragraphs, and a clear call-to-action closing.",
    },
}

# ---------- MASTER PROMPT TEMPLATE (the "locked" brand-safe template) ----------
def build_prompt(product_name, platform, tone, extra_details):
    rules = PLATFORM_RULES[platform]
    prompt = f"""You are a professional marketing copywriter.

Product: {product_name}
Platform: {platform}
Tone: {tone}
Additional details: {extra_details if extra_details else "None provided"}

Platform-specific rules: {rules['instructions']}
Strict character limit: {rules['limit']} characters.

Generate ONLY the final marketing copy. Do not include any preamble, explanation, or notes. Output the copy text only."""
    return prompt

# ---------- SESSION STATE FOR HISTORY ----------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("✨ Copy Transformer")
    st.caption("Automated Copywriting & Tone Transformer — Decode Labs Project 2")
    st.divider()

    product_name = st.text_input("Product Name", placeholder="e.g. Wireless Noise-Cancelling Headphones")
    extra_details = st.text_area("Extra details (optional)", placeholder="e.g. 30hr battery, ₹4999, launching Friday", height=80)

    platform = st.selectbox("Platform", list(PLATFORM_RULES.keys()))
    tone = st.selectbox("Tone", list(TONE_SETTINGS.keys()))

    st.divider()
    st.subheader("Advanced — Inference Parameters")
    default_temp = TONE_SETTINGS[tone]["temperature"]
    default_top_p = TONE_SETTINGS[tone]["top_p"]

    override = st.checkbox("Override default tone settings")
    if override:
        temperature = st.slider("Temperature (creativity)", 0.0, 1.0, default_temp, 0.05)
        top_p = st.slider("Top_P", 0.0, 1.0, default_top_p, 0.05)
    else:
        temperature = default_temp
        top_p = default_top_p
        st.info(f"Using {tone} defaults — Temp: {temperature}, Top_P: {top_p}")

    st.divider()
    compare_mode = st.checkbox("Compare across all platforms")
    generate_btn = st.button("Generate Copy 🚀", type="primary", use_container_width=True)

# ---------- MAIN AREA ----------
st.header("Automated Copywriting & Tone Transformer")
st.caption("Generate platform-tailored marketing copy from a single product description.")

def call_model(prompt, temperature, top_p):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_p,
        max_tokens=600,
    )
    return response.choices[0].message.content

if generate_btn:
    if not product_name.strip():
        st.error("Please enter a product name before generating.")
    else:
        if compare_mode:
            st.subheader(f"Comparing all platforms — Tone: {tone}")
            cols = st.columns(len(PLATFORM_RULES))
            for i, plat in enumerate(PLATFORM_RULES.keys()):
                with cols[i]:
                    st.markdown(f"**{plat}**")
                    with st.spinner(f"Generating {plat} copy..."):
                        prompt = build_prompt(product_name, plat, tone, extra_details)
                        result = call_model(prompt, temperature, top_p)
                    char_count = len(result)
                    limit = PLATFORM_RULES[plat]["limit"]
                    st.text_area(f"{plat} output", result, height=250, key=f"compare_{plat}")
                    if char_count > limit:
                        st.error(f"{char_count}/{limit} chars — exceeds limit!")
                    else:
                        st.success(f"{char_count}/{limit} chars — within limit")
                    st.session_state.history.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "product": product_name,
                        "platform": plat,
                        "tone": tone,
                        "output": result,
                    })
        else:
            with st.spinner(f"Generating {platform} copy with {tone} tone..."):
                prompt = build_prompt(product_name, platform, tone, extra_details)
                result = call_model(prompt, temperature, top_p)

            char_count = len(result)
            limit = PLATFORM_RULES[platform]["limit"]

            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{platform} — {tone} tone")
            with col2:
                if char_count > limit:
                    st.error(f"{char_count}/{limit} chars")
                else:
                    st.success(f"{char_count}/{limit} chars")

            st.text_area("Generated Copy", result, height=250)
            st.download_button("Download as .txt", result, file_name=f"{product_name}_{platform}_{tone}.txt")

            st.session_state.history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "product": product_name,
                "platform": platform,
                "tone": tone,
                "output": result,
            })

# ---------- HISTORY PANEL ----------
st.divider()
st.subheader("📜 Generation History (this session)")

if not st.session_state.history:
    st.caption("No copy generated yet. Fill the form on the left and click Generate.")
else:
    for item in reversed(st.session_state.history):
        with st.expander(f"{item['time']} · {item['product']} · {item['platform']} · {item['tone']}"):
            st.write(item["output"])

    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
