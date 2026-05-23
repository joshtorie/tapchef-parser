import streamlit as st
import json
import pandas as pd
import psycopg
from database import init_local_tables, save_parsed_recipe, CONN_STR
from parser import parse_raw_recipe
from recipe_scrapers import scrape_me
from models import RecipeSchema

st.set_page_config(page_title="TapChef Parser Ingestion Hub", layout="wide")

st.title("🍳 TapChef Kitchen OS Ingestion Engine")
st.markdown("---")

# 1. Automatically initialize database tables on bootup
if "db_initialized" not in st.session_state:
    try:
        init_local_tables()
        st.session_state.db_initialized = True
        st.sidebar.success("💻 Local PostgreSQL Connected Successfully")
    except Exception as e:
        st.sidebar.error(f"❌ Database Connection Failed: {e}")

# 2. Sidebar Configuration View
st.sidebar.header("Configuration Panel")
st.sidebar.info("Currently running on your local home server.")

# 3. Main GUI Tabs
tab1, tab2 = st.tabs(["📥 Ingest Recipe Data", "🗂️ View Local Database"])

with tab1:
    st.subheader("🔬 AI Prompt Optimization & Stress-Testing Sandbox")
    url_pool_raw = st.text_area(
        "Testing Pool URLs (One per line):",
        height=150,
        placeholder="https://www.seriouseats.com/recipe-1"
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
            if st.button("Extract Raw Text from Site", type="secondary", width='stretch'):
                with st.spinner("Fetching..."):
                    scraper = scrape_me(selected_target_url)
                    text_payload = f"Title: {scraper.title()}\n\nIngredients:\n" + "\n".join(scraper.ingredients()) + "\n\nInstructions:\n" + scraper.instructions()
                    st.session_state[f"raw_text_{selected_target_url}"] = text_payload
            
            if f"raw_text_{selected_target_url}" in st.session_state:
                st.text_area("Raw Markdown:", st.session_state[f"raw_text_{selected_target_url}"], height=500)

        with col_right:
            st.markdown("### 🧠 Step 2: AI Tokenization Matrix")
            if st.button("Run Parser Prompt", type="primary", width='stretch'):
                with st.spinner("Executing parser..."):
                    structured_recipe = parse_raw_recipe(st.session_state[f"raw_text_{selected_target_url}"], selected_target_url)
                    st.session_state[f"json_output_{selected_target_url}"] = structured_recipe.model_dump()
            
            if f"json_output_{selected_target_url}" in st.session_state:
                st.json(st.session_state[f"json_output_{selected_target_url}"])
                if st.button("Commit to Local DB", type="secondary", width='stretch'):
                    save_parsed_recipe(RecipeSchema(**st.session_state[f"json_output_{selected_target_url}"]), selected_target_url)
                    st.success("Committed to registry.")
    else:
        st.info("Input your target testing list above.")

with tab2:
    st.subheader("🗂️ Database Record Verification")
    
    try:
        with psycopg.connect(CONN_STR) as conn:
            query = "SELECT id, title, source_url, steps FROM local_recipes ORDER BY created_at DESC;"
            df = pd.read_sql(query, conn)
            
        if df.empty:
            st.info("No recipes found. Run the parser to ingest data.")
        else:
            selected_recipe_title = st.selectbox("Select recipe to inspect:", df["title"].unique())
            matched_row = df[df["title"] == selected_recipe_title].iloc[0]
            
            steps = matched_row["steps"]
            for step in steps:
                # UPDATED: Using step_summary for display
                summary = step.get("step_summary", "Untitled Step")
                with st.expander(f"Step {step['step_number']}: {summary[:60]}...", expanded=False):
                    
                    # NEW: Atomic Actions Display
                    st.write("#### 📝 Atomic Execution List")
                    for act in step.get("actions", []):
                        icon = "👉"
                        if act['action_type'] == 'add': icon = "➕"
                        elif act['action_type'] == 'cook': icon = "🍳"
                        elif act['action_type'] == 'wait': icon = "⏳"
                        elif act['action_type'] == 'transfer': icon = "↪️"
                        elif act['action_type'] == 'season': icon = "🧂"
                        
                        if act.get('is_timer'):
                            st.warning(f"{icon} **{act['text']}** — *{act['duration_minutes']} min timer*")
                        else:
                            st.markdown(f"{icon} {act['text']}")

                    st.markdown("---")
                    
                    # Columns for metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write("#### 🍳 Cookware")
                        st.json(step.get("cookware", []))
                    
                    with col2:
                        st.write("#### 🛠️ Implements")
                        st.json(step.get("implements", []))
                        
                    with col3:
                        st.write("#### 🌡️ Heat Sequence")
                        for phase in step.get("heat_phases", []):
                            st.info(f"**{phase.get('heat_setting', 'N/A').upper()}** → {phase.get('target_state', 'N/A')}")
                            st.caption(f"Context: {phase.get('duration_context', 'N/A')}")
                            
                    with col4:
                        st.write("#### 🥦 Ingredients")
                        st.json(step.get("ingredients_used", []))
                        if step.get("target_temperature"):
                            st.write(f"**Fixed Temp:** {step['target_temperature']}{step.get('temp_unit')}")
                    
    except Exception as db_view_err:
        st.error(f"Failed to read indexed table rows: {db_view_err}")