import streamlit as st
import json
import pandas as pd
import time
from parser import parse_raw_recipe
from recipe_scrapers import scrape_me
from models import RecipeSchema

st.set_page_config(page_title="TapChef Parser Ingestion Hub", layout="wide")

st.title("🍳 TapChef Kitchen OS Ingestion Engine")
st.markdown("---")

# Sidebar Configuration View
st.sidebar.header("Configuration Panel")
st.sidebar.info("Currently running on your local home server with direct memory state transmission (No Database Required).")

# 1. Main GUI Tabs
tab1, tab3 = st.tabs(["📥 Ingest Recipe Data", "🍳 Active Kitchen Instructions"])

with tab1:
    st.subheader("🔬 AI Prompt Optimization & Stress-Testing Sandbox")
    url_pool_raw = st.text_area(
        "Testing Pool URLs (One per line):",
        height=150,
        placeholder="https://www.seriouseats.com/recipe-1",
        key="pool_urls"
    )

    test_urls = [line.strip() for line in url_pool_raw.split("\n") if line.strip()]

    if test_urls:
        st.markdown("---")
        current_index = 0
        if "last_selected_url" in st.session_state and st.session_state.last_selected_url in test_urls:
            current_index = test_urls.index(st.session_state.last_selected_url)

        selected_target_url = st.selectbox("🎯 Choose a specific URL:", test_urls, index=current_index)
        st.session_state.last_selected_url = selected_target_url

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### 🌐 Step 1: Scraped Context")
            if st.button("Extract Raw Text from Site", type="secondary", use_container_width=True):
                with st.spinner("Fetching..."):
                    scraper = scrape_me(selected_target_url)
                    text_payload = f"Title: {scraper.title()}\n\nIngredients:\n" + "\n".join(scraper.ingredients()) + "\n\nInstructions:\n" + scraper.instructions()
                    st.session_state[f"raw_text_{selected_target_url}"] = text_payload
                    st.session_state[f"title_{selected_target_url}"] = scraper.title()
            
            if f"raw_text_{selected_target_url}" in st.session_state:
                st.text_area("Raw Markdown:", st.session_state[f"raw_text_{selected_target_url}"], height=500)

        with col_right:
            st.markdown("### 🧠 Step 2: AI Tokenization Matrix")
            if st.button("Run Parser Prompt", type="primary", use_container_width=True):
                with st.spinner("Executing parser..."):
                    structured_recipe = parse_raw_recipe(st.session_state[f"raw_text_{selected_target_url}"], selected_target_url)
                    st.session_state[f"json_output_{selected_target_url}"] = structured_recipe.model_dump()
            
            if f"json_output_{selected_target_url}" in st.session_state:
                st.json(st.session_state[f"json_output_{selected_target_url}"])
                
                # CHANGED: Push directly to active cooking state rather than connecting to db
                if st.button("🚀 Send to Active Cooking Tab", type="secondary", use_container_width=True):
                    recipe_data = st.session_state[f"json_output_{selected_target_url}"]
                    st.session_state["active_recipe_title"] = recipe_data.get("title", st.session_state.get(f"title_{selected_target_url}", "Ingested Recipe"))
                    st.session_state["active_recipe_steps"] = recipe_data.get("steps", [])
                    st.session_state["active_step_idx"] = 0  # Reset cooking to beginning
                    st.success("Recipe pushed to Cooking Tab! Switch tabs above to execute.")
    else:
        st.info("Input your target testing list above.")


# 2. Active Cooking Instructions Tab Framework (Powered by session_state memory)
with tab3:
    st.subheader("👨‍🍳 Hands-Free Active Cooking Dashboard")
    
    # Check if a recipe has been explicitly pushed into application memory cache
    if "active_recipe_steps" not in st.session_state or not st.session_state["active_recipe_steps"]:
        st.info("No active recipe running in execution memory. Go to the 'Ingest Recipe Data' tab, parse a recipe, and click 'Send to Active Cooking Tab'.")
    else:
        active_recipe_name = st.session_state["active_recipe_title"]
        active_recipe_steps = st.session_state["active_recipe_steps"]
        
        # Tracking current active cooking indexes inside session state
        if "active_step_idx" not in st.session_state:
            st.session_state.active_step_idx = 0
            
        current_idx = st.session_state.active_step_idx
        current_step = active_recipe_steps[current_idx]
        
        st.caption(f"Executing Recipe: **{active_recipe_name}**")
        
        # --- UI NAVIGATION PANEL CONTROLS ---
        col_prev, col_status, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Previous Step", use_container_width=True, key="cooking_prev_btn") and current_idx > 0:
                st.session_state.active_step_idx -= 1
                st.rerun()
        with col_status:
            st.markdown(f"<h3 style='text-align: center;'>Step {current_idx + 1} of {len(active_recipe_steps)}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: gray;'><i>{current_step.get('step_summary', '')}</i></p>", unsafe_allow_html=True)
        with col_next:
            if st.button("Next Step ➡️", use_container_width=True, key="cooking_next_btn") and current_idx < len(active_recipe_steps) - 1:
                st.session_state.active_step_idx += 1
                st.rerun()
                
        st.markdown("---")
        
        # --- MAIN INSTRUCTION DISPLAY ---
        st.info("🗣️ **Active Instruction Text:**")
        st.markdown(f"<h2 style='line-height: 1.5;'>{current_step.get('step_description', 'No descriptive text provided.')}</h2>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- METADATA DISPLAY PANELS (Ingredients, Implements, Cookware) ---
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        
        with meta_col1:
            st.markdown("#### 🥦 Ingredients in Use")
            ingredients = current_step.get("ingredients_used", [])
            if ingredients:
                for ing in ingredients:
                    name = ing.get("name", "Unknown Ingredient")
                    amt = f" ({ing['amount']} {ing['unit']})" if ing.get("amount") else ""
                    st.write(f"- {name}{amt}")
            else:
                st.caption("No explicit ingredients referenced here.")
                
        with meta_col2:
            st.markdown("#### 🛠️ Implements Used")
            implements = current_step.get("implements", [])
            if implements:
                for imp in implements:
                    st.write(f"- 🧰 {imp.replace('_', ' ').title()}")
            else:
                st.caption("No loose tools/implements designated.")
                
        with meta_col3:
            st.markdown("#### 🍳 Cookware In Use")
            cookware = current_step.get("cookware", [])
            if cookware:
                for cw in cookware:
                    st.write(f"- 🍳 {cw.replace('_', ' ').title()}")
            else:
                st.caption("No heavy cookware assigned.")
                
        st.markdown("---")
        
        # --- AUTOMATIC TIMERS ENGINE PANEL ---
        st.markdown("#### ⏱️ Step Hardware Timers")
        # Extracting duration triggers directly from atomic action arrays containing flags
        timer_actions = [a for a in current_step.get("actions", []) if a.get("is_timer") and a.get("duration_minutes", 0) > 0]
        
        if timer_actions:
            for idx, t_action in enumerate(timer_actions):
                minutes = float(t_action["duration_minutes"])
                st.warning(f"🔔 **Timer Detected:** {t_action['text']} ({minutes} Minutes)")
                
                # Generate dynamic execution token mapping keys
                timer_key = f"timer_running_{current_idx}_{idx}"
                if timer_key not in st.session_state:
                    st.session_state[timer_key] = False
                    
                if st.button(f"▶️ Start Timer ({minutes}m)", key=f"btn_{timer_key}"):
                    st.session_state[timer_key] = True
                    
                if st.session_state[timer_key]:
                    placeholder = st.empty()
                    total_seconds = int(minutes * 60)
                    
                    # Process loops running directly through active countdown frames
                    for remaining in range(total_seconds, -1, -1):
                        m, s = divmod(remaining, 60)
                        placeholder.metric(label="⌛ Time Remaining", value=f"{m:02d}:{s:02d}")
                        time.sleep(1)
                    st.toast("🚨 Timer finished!", icon="⏰")
                    st.balloons()
                    st.session_state[timer_key] = False
        else:
            st.success("⚡ Manual Action Step: No automatic countdown constraints mapped to this phase.")
            
        # --- KEYBOARD NAVIGATION (ENTER KEY ADVANCEMENT HOOKS) ---
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.form(key="keyboard_nav_form_container", clear_on_submit=True):
            st.caption("💡 Kitchen Tip: Click inside the input below and hit **Enter** to instantly jump to the next step.")
            nav_trigger = st.text_input("Keyboard Shortcut Hub:", label_visibility="collapsed", placeholder="Hit Enter to go next...")
            submit_nav = st.form_submit_button("Advance Sequence", hidden=True)
            
            if submit_nav:
                if current_idx < len(active_recipe_steps) - 1:
                    st.session_state.active_step_idx += 1
                    st.rerun()