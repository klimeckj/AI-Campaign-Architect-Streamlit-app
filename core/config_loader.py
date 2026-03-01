"""Configuration and prompt loading utilities."""
import json
import os
import streamlit as st


def load_config():
    """Load configuration from st.secrets (Streamlit Cloud) or config.json (local)."""
    # --- Streamlit Cloud: read from st.secrets ---
    try:
        if "GEMINI_API_KEY" in st.secrets:
            config = {
                "GEMINI_API_KEY": st.secrets["GEMINI_API_KEY"],
            }
            if "bloomreach" in st.secrets:
                br = st.secrets["bloomreach"]
                config["bloomreach"] = {
                    "api_base_url": br["api_base_url"],
                    "project_token": br["project_token"],
                    "catalog_id": br["catalog_id"],
                    "auth_key_id": br["auth_key_id"],
                    "auth_key_secret": br["auth_key_secret"],
                }
            return config
    except Exception:
        pass  # st.secrets not available — fall back to config.json

    # --- Local development: read from config.json ---
    config_file = "config.json"
    if not os.path.exists(config_file):
        return None
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Chyba při čtení config.json: {e}")
        return None


def load_prompts():
    """Load prompt templates from prompts.json."""
    prompts_file = "prompts.json"
    if not os.path.exists(prompts_file):
        # Fallback on default prompts
        return {
            "strategy": "Jsi Marketing Strategist. Produkt: {product}, Cílovka: {target}, USP: {goal}. Napiš stručnou strategii (Markdown): Analýza, Angle, Tone of Voice. Česky.",
            "copywriter": "Jsi Copywriter. Strategie: {strategy}. Úkol: Napiš JSON objekt (bez markdownu) pro: {{ \"email_subject\": \"\", \"email_body\": \"\", \"sms_text\": \"\", \"push_text\": \"\" }} SMS max 160 znaků. Česky."
        }
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {key: val.get("template") for key, val in data.get("prompts", {}).items()}
    except Exception as e:
        st.warning(f"Chyba při čtení prompts.json: {e}. Používám výchozí prompty.")
        return {
            "strategy": "Jsi Marketing Strategist. Produkt: {product}, Cílovka: {target}, USP: {goal}. Napiš stručnou strategii (Markdown): Analýza, Angle, Tone of Voice. Česky.",
            "copywriter": "Jsi Copywriter. Strategie: {strategy}. Úkol: Napiš JSON objekt (bez markdownu) pro: {{ \"email_subject\": \"\", \"email_body\": \"\", \"sms_text\": \"\", \"push_text\": \"\" }} SMS max 160 znaků. Česky."
        }
