import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIG & STYLING ---
st.set_page_config(page_title="GitHub Analyzer", page_icon="🚀", layout="wide")

# CSS to remove the Deploy button, keep 3-dots, and strip out top blank spacing padding completely
st.markdown("""
    <style>
        /* Hide Deploy button variants */
        .stAppDeployButton, 
        div[data-testid="stActionButton"], 
        .stDeployButton {
            display: none !important;
        }
        /* Remove blank vertical spaces at the top of the app page */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
        }
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Centered App Title and Subtitle Header
st.markdown("""
    <div style="text-align: center;">
        <h1>🚀 GitHub Analyzer</h1>
        <p style="font-size: 1.15rem; color: #A0AEC0;">Analyze any GitHub profile and get tailored optimization suggestions instantly.</p>
    </div>
""", unsafe_allow_html=True)

# Centered input text bar layout using columns block configuration
_, input_col, _ = st.columns([1.5, 2, 1.5])
with input_col:
    username = st.text_input("Enter GitHub Username", placeholder="e.g., alice-smith1234")

if username.strip():
    with st.spinner("Fetching GitHub data in real-time..."):
        # Fetch Profile Data
        p_res = requests.get(f"https://api.github.com/users/{username}")
        
        if p_res.status_code == 403:
            st.error("⚠️ GitHub API Rate Limit Exceeded. Please try again later or add an Auth Token.")
            st.stop()
        elif p_res.status_code != 200:
            st.error("🔍 GitHub user not found. Double-check the spelling.")
            st.stop()
            
        profile = p_res.json()
        
        # Fetch Repositories Data
        r_res = requests.get(profile.get("repos_url", ""))
        if r_res.status_code == 200:
            repos = r_res.json()
            # Ensure repos is a list, not an error dict
            if not isinstance(repos, list):
                repos = []
        else:
            repos = []

    st.success("Analysis Completed!")
    
    # --- SHOW PROFILE ---
    st.header("👤 GitHub Profile")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(profile.get("avatar_url", ""), width=150)
    with col2:
        st.write(f"### {profile.get('name') or username}")
        st.write(profile.get("bio") or "No bio available.")
        joined_date = profile.get('created_at', '')[:10] if profile.get('created_at') else "Unknown"
        st.write(f"🌐 GitHub Profile: {profile.get('html_url','')}\n\n📅 Joined: {joined_date}")
    st.divider()

    # --- PROCESS DATA & SHOW STATISTICS ---
    total_stars = sum(r.get("stargazers_count", 0) for r in repos) if isinstance(repos, list) else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Repositories", profile.get("public_repos", 0))
    c2.metric("Followers", profile.get("followers", 0))
    c3.metric("Following", profile.get("following", 0))
    c4.metric("Total Stars", total_stars)

    # --- PROCESS REPOSITORIES & LANGUAGES ---
    languages = {}
    repo_data = []
    
    for r in repos:
        repo_data.append({
            "Repository": r.get("name"), 
            "Language": r.get("language") or "Unknown",
            "Stars": r.get("stargazers_count", 0), 
            "Forks": r.get("forks_count", 0), 
            "URL": r.get("html_url")
        })
        if r.get("language"):
            languages[r["language"]] = languages.get(r["language"], 0) + 1

    df = pd.DataFrame(repo_data)
    
    # --- REAL-TIME SCORE CALCULATION ---
    score = 40
    score += 15 if profile.get("public_repos", 0) >= 10 else 0
    score += 15 if profile.get("followers", 0) >= 20 else 0
    score += 15 if total_stars >= 30 else 0
    score += sum(5 for k in ["bio", "blog", "location", "company"] if profile.get(k))
    score = min(score, 100)

    st.header("🏆 Real-Time GitHub Score")
    st.progress(score / 100)
    st.success(f"Portfolio Score: {score}/100")

    # --- DISPLAY REPOSITORY DETAILS ---
    st.header("📂 Repository Details")
    if df.empty:
        st.warning("No public repositories found.")
    else:
        st.dataframe(df, use_container_width=True)
        top_repo = df.sort_values("Stars", ascending=False).iloc[0]
        st.subheader("⭐ Top Repository")
        st.write(f"**{top_repo['Repository']}**\n\n⭐ Stars: {top_repo['Stars']} | 🍴 Forks: {top_repo['Forks']}\n\n{top_repo['URL']}")

    # --- DISPLAY LANGUAGES (COMPACT & CLEAN PIE CHART) ---
    st.header("💻 Languages Used")
    if languages:
        chart_col, _ = st.columns([1.2, 2.8])
        with chart_col:
            fig, ax = plt.subplots(figsize=(2.5, 2.5))
            fig.patch.set_facecolor('none')
            ax.set_facecolor('none')
            
            custom_colors = ['#319795', '#4A5568', '#48BB78', '#F56565', '#ED8936', '#667EEA']
            
            wedges, texts, autotexts = ax.pie(
                languages.values(),
                labels=languages.keys(),
                autopct="%1.0f%%",
                startangle=90,
                colors=custom_colors * (len(languages) // len(custom_colors) + 1),
                textprops={'fontsize': 8, 'color': '#A0AEC0'}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(7)
                
            ax.axis('equal')  
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    else:
        st.info("No language information available.")

    # --- DYNAMIC CUSTOM ACCOUNT SUGGESTIONS (MAX 10 WORDS EACH) ---
    st.header("📌 Custom Portfolio Suggestions")
    has_suggestions = False
    
    public_repos = profile.get("public_repos", 0)
    if public_repos < 5:
        st.error("⚠️ Low Repositories: Upload more projects to show your technical skills.")
        has_suggestions = True
        
    if total_stars == 0 and public_repos > 0:
        st.warning("💡 No Stars: Add detailed README files with clear project screenshots.")
        has_suggestions = True
    elif total_stars > 0 and (total_stars / max(public_repos, 1)) < 0.5:
        st.info("📌 Pin Best Work:Pin your top 3 projects to your homepage.")
        has_suggestions = True

    if not profile.get("bio"):
        st.warning("👤 Missing Bio: Add a short bio describing your core tech stack.")
        has_suggestions = True

    if not profile.get("blog"):
        st.info("🌐 No Links: Add your portfolio or LinkedIn link to your profile.")
        has_suggestions = True

    if profile.get("followers", 0) > 50 and public_repos < 5:
        st.warning("📈 Share Code: Publish more public projects for your growing audience.")
        has_suggestions = True
        
    if not has_suggestions:
        st.success("🌟 Great Profile: Your GitHub account is well-optimized and looking solid!!!")

    # --- CONTRIBUTION GRAPH ---
    st.header("📅 GitHub Contribution Graph")
    st.image(f"https://ghchart.rshah.org/319795/{username}")