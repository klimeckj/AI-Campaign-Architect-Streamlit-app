import streamlit as st
import pandas as pd
import json
import uuid

# Import core modules
from core.config_loader import load_config, load_prompts
from core.genai_service import GeminiClient, generate_content_safe, refine_content, extract_json_from_response, mock_strategy_response, mock_copy_generation
from core.bloomreach_service import push_to_bloomreach
from core.utils import init_session_state, validate_sms_length, validate_segment_id

# ==========================================
# KONFIGURACE A SESTAVENÍ STRÁNKY
# ==========================================
st.set_page_config(
    page_title="AI Campaign Architect (NextGen)",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { background-color: #0084ff; color: white; border-radius: 5px; font-weight: bold; }
    .stSuccess { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    h1 { color: #2c3e50; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# FUNKCE: NAČTENÍ KONFIGURACE A KLIENTA
# ---------------------------------------------------------
config = load_config()
prompts = load_prompts()

def init_genai_client(config):
    """Inicializace Google GenAI klienta."""
    if not config:
        return None
    api_key = config.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return GeminiClient(api_key=api_key, model_id="gemma-3-1b-it")

# Globální klient
client = init_genai_client(config)

# ---------------------------------------------------------
# FUNKCE: BLOOMREACH API INTEGRACE
# ---------------------------------------------------------
# Integrated in core/bloomreach_service.py

# ---------------------------------------------------------
# FUNKCE: GENERUJÍCÍ LOGIKA (GEMINI)
# ---------------------------------------------------------
# Integrated in core/genai_service.py

# ==========================================
# UI LOGIKA APLIKACE
# ==========================================
def main():
    st.title("AI Campaign Architect 2.0 s integrací Demo Bloomreach")

    # Initialize session state
    init_session_state()

    # --- STEP 1: ZADÁNÍ ---
    st.subheader("1. Zadání (Brief)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.text_input("Produkt", value=st.session_state.brief.get('product', ''))
    with col2:
        # ZMĚNA: Ruční zadání Segment ID
        t = st.text_input("Popis cílovky", value=st.session_state.brief.get('target', ''))
    with col3:
        # Nové pole pro technické ID segmentu
        seg_id = st.text_input("Segment ID (Bloomreach)", value=st.session_state.brief.get('segment_id', ''))

    g = st.text_area("Cíl / USP", value=st.session_state.brief.get('goal', ''))

    if st.button("Analyzovat"):
        valid_segment, msg = validate_segment_id(seg_id)
        if not valid_segment:
            st.warning(f"{msg}")
        else:
            st.session_state.brief = {'product': p, 'target': t, 'goal': g, 'segment_id': seg_id}
            st.session_state.stage = 1
            st.rerun()

    # --- STEP 2: STRATEGIE ---
    if st.session_state.stage >= 1:
        st.markdown("---")
        st.subheader("2. Strategie")
        
        if 'strategy_output' not in st.session_state or st.session_state.strategy_output is None:
            with st.spinner('Gemini přemýšlí...'):
                prompt = prompts["strategy"].format(product=p, target=t, goal=g)
                try:
                    st.session_state.strategy_output = generate_content_safe(client, prompt)
                except Exception as e:
                    st.error(f"Chyba: {e}")
                    st.session_state.strategy_output = mock_strategy_response(p, t)

        with st.expander("Zobrazit strategii"):
            st.markdown(st.session_state.strategy_output)
        
        # === REFINEMENT LOOP: STRATEGIE ===
        st.markdown("##### Iterativní zpřesňování")
        col_ref1, col_ref2 = st.columns([3, 1])
        with col_ref1:
            strategy_feedback = st.text_input(
                "Máš připomínku? (př. 'Přidej obsah o ceně', 'Víc emocí')",
                placeholder="Napiš co chceš změnit...",
                key="strategy_feedback_input"
            )
        with col_ref2:
            st.write("")  # Spacing
            if st.button("Zapracovat", key="strategy_refine_btn"):
                if strategy_feedback.strip():
                    with st.spinner('AI upravuje...'):
                        try:
                            refinement_prompt = prompts["strategy_refinement"].format(
                                product=p,
                                target=t,
                                goal=g,
                                current_draft=st.session_state.strategy_output,
                                feedback=strategy_feedback
                            )
                            st.session_state.strategy_output = refine_content(client, "", refinement_prompt)
                            st.success("Strategie byla upravena!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chyba při úpravě: {e}")
                else:
                    st.warning("Napiš svou připomínku!")
        
        st.markdown("---")
        
        if st.button("Schválit strategii"):
            st.session_state.stage = 2
            st.rerun()

    # --- STEP 3: OBSAH & EXPORT ---
    if st.session_state.stage >= 2:
        st.markdown("---")
        st.subheader("3. Generování Obsahu")
        
        if not st.session_state.generated_content:
            with st.spinner('Píšu copy...'):
                prompt = prompts["copywriter"].format(strategy=st.session_state.strategy_output)
                try:
                    text_resp = generate_content_safe(client, prompt)
                    clean = text_resp.replace("```json", "").replace("```", "").strip()
                    content_json = json.loads(clean)
                    
                    # Přidáme metadata pro export
                    content_json['item_id'] = st.session_state.current_item_id
                    content_json['segment_id'] = st.session_state.brief['segment_id']
                    
                    st.session_state.generated_content = content_json
                except Exception as e:
                    st.error(f"Chyba generování copy: {e}")
                    st.session_state.generated_content = mock_copy_generation(p)

        c = st.session_state.generated_content
        
        # UI Editace
        tab1, tab2, tab3, tab4 = st.tabs(["Email", "SMS", "Push", "Data Preview"])
        with tab1:
            c['email_subject'] = st.text_input("Předmět", value=c.get('email_subject'))
            c['email_body'] = st.text_area("Tělo", value=c.get('email_body'), height=200)
            
            # === REFINEMENT: EMAIL ===
            with st.expander("Upravit tuto zprávu"):
                email_feedback = st.text_input(
                    "Popis změny:",
                    placeholder="Př. 'Přidej emoji', 'Zkrať na 100 slov', 'Tykej si'",
                    key="email_feedback"
                )
                if st.button("Zapracovat feedback", key="email_refine_btn"):
                    if email_feedback.strip():
                        with st.spinner('AI upravuje email...'):
                            try:
                                refinement_prompt = prompts["email_refinement"].format(
                                    strategy=st.session_state.strategy_output,
                                    email_subject=c.get('email_subject', ''),
                                    email_body=c.get('email_body', ''),
                                    feedback=email_feedback
                                )
                                
                                refined_text = refine_content(client, "", refinement_prompt)
                                refined_json = extract_json_from_response(refined_text)
                                
                                c['email_subject'] = refined_json.get('email_subject', c.get('email_subject'))
                                c['email_body'] = refined_json.get('email_body', c.get('email_body'))
                                
                                st.session_state.generated_content = c
                                st.success("Email byl upraven!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba: {str(e)}")
                    else:
                        st.warning("Napiš co chceš změnit!")
        
        with tab2:
            c['sms_text'] = st.text_area("SMS", value=c.get('sms_text'))
            sms_valid, sms_msg = validate_sms_length(c.get('sms_text', ''))
            if sms_valid:
                st.caption(f"Znaků: {len(c.get('sms_text', ''))}/160")
            else:
                st.error(sms_msg)
            
            # === REFINEMENT: SMS ===
            with st.expander("Upravit tuto zprávu"):
                sms_feedback = st.text_input(
                    "Popis změny:",
                    placeholder="Př. 'Zkrať', 'Přidej urgenci', 'Víc formální'",
                    key="sms_feedback"
                )
                if st.button("Zapracovat feedback", key="sms_refine_btn"):
                    if sms_feedback.strip():
                        with st.spinner('AI upravuje SMS...'):
                            try:
                                refinement_prompt = prompts["sms_refinement"].format(
                                    strategy=st.session_state.strategy_output,
                                    sms_text=c.get('sms_text', ''),
                                    feedback=sms_feedback
                                )
                                
                                refined_text = refine_content(client, "", refinement_prompt)
                                refined_json = extract_json_from_response(refined_text)
                                
                                c['sms_text'] = refined_json.get('sms_text', c.get('sms_text'))
                                
                                st.session_state.generated_content = c
                                st.success("SMS byl upraven!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba: {str(e)}")
                    else:
                        st.warning("Napiš co chceš změnit!")
        
        with tab3:
            c['push_text'] = st.text_area("Push", value=c.get('push_text'))
            
            # === REFINEMENT: PUSH ===
            with st.expander("Upravit tuto zprávu"):
                push_feedback = st.text_input(
                    "Popis změny:",
                    placeholder="Př. 'Přidej CTA', 'Více slev', 'Zkrať'",
                    key="push_feedback"
                )
                if st.button("Zapracovat feedback", key="push_refine_btn"):
                    if push_feedback.strip():
                        with st.spinner('AI upravuje push...'):
                            try:
                                refinement_prompt = prompts["push_refinement"].format(
                                    strategy=st.session_state.strategy_output,
                                    push_text=c.get('push_text', ''),
                                    feedback=push_feedback
                                )
                                
                                refined_text = refine_content(client, "", refinement_prompt)
                                refined_json = extract_json_from_response(refined_text)
                                
                                c['push_text'] = refined_json.get('push_text', c.get('push_text'))
                                
                                st.session_state.generated_content = c
                                st.success("Push byl upraven!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba: {str(e)}")
                    else:
                        st.warning("Napiš co chceš změnit!")
        
        with tab4:
            st.json({
                "item_id": c.get('item_id'), 
                "segment_id": c.get('segment_id')
            })
            if st.button("Vygenerovat nové ID varianty"):
                st.session_state.current_item_id = str(uuid.uuid4())
                c['item_id'] = st.session_state.current_item_id
                st.rerun()

        # Aktualizace session state po editaci
        st.session_state.generated_content = c

        # --- EXPORT & INTEGRACE ---
        st.markdown("---")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            # CSV Export
            df = pd.DataFrame([c])
            st.download_button("Stáhnout CSV", df.to_csv(index=False).encode('utf-8'), "campaign_elevon.csv")
            
        with col_exp2:
            # Bloomreach Upload
            if st.button("Odeslat do Bloomreach"):
                with st.spinner("Nalévám data do katalogu..."):
                    success, msg = push_to_bloomreach(config, c)
                    if success:
                        st.success(f"Hotovo! Data jsou v katalogu. \nID: {c['item_id']}")
                    else:
                        st.error(f"Chyba nahrávání: {msg}")

if __name__ == "__main__":
    main()