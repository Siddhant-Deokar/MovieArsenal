import streamlit as st
import pickle
import pandas as pd





if 'uid' not in st.session_state:
    st.session_state.uid = None    

    
if "onboarding_recs" not in st.session_state:
    st.session_state.onboarding_recs = None

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
    
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False

st.set_page_config(layout="wide")

@st.cache_resource
def load_movie_options():
    df = pd.read_csv("display_movie_data.csv")

    movie_options = df['title'].unique().tolist()

    return df,movie_options



@st.dialog("Movie Details")
def show_movie_details(movie):
    
    
    col_img, col_info = st.columns([1.5, 2.5])  # bigger image

    with col_img:
        st.image(movie['poster_url'], width='stretch')

    with col_info:
        st.subheader(movie['title'])

        st.markdown(f"""
<div style="
    display: grid; 
    grid-template-columns: 120px 1fr; 
    row-gap: 8px;
    line-height: 1.4;
">

<div><b>Language:</b></div><div>{movie['original_language']}</div>

<div><b>Genre:</b></div><div>{movie['genre']}</div>

<div><b>Production:</b></div><div>{movie['production_companies']}</div>

<div><b>Director:</b></div><div>{movie['director']}</div>

<div><b>Cast:</b></div><div>{', '.join(movie['cast'].split(', ')[:4])}</div>

</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    st.write(movie.get('overview', 'No description available'))



def print_row(df, title):

    cols = st.columns(5)

    for i in range(len(df)): 
        with cols[i]:
            st.image(df.iloc[i,10])
            st.markdown(f"""
                <div style="
                    height: 60px;
                    overflow: hidden;
                    font-size: 18px;
                ">
                {df.iloc[i,1]}
                </div>
            """, unsafe_allow_html=True)

            if st.button("View", key=f"{title}_{df.iloc[i]['MovieID']}"):
                st.session_state.selected_movie = df.iloc[i]
                st.session_state.show_dialog = True
                    





st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
st.markdown("""
<style>
/* Target top navigation buttons */
div[data-testid="stHorizontalBlock"] > div button {
    font-size: 20px !important;
    padding: 10px 18px !important;
    border-radius: 8px !important;
}

/* Active tab */
div[data-testid="stHorizontalBlock"] > div button[aria-selected="true"] {
    font-weight: bold;
    background-color: #2a2b32 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.block-container {
    padding-top: 0.2rem !important;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}
</style>
""", unsafe_allow_html=True)


# -------- NAV --------
if st.session_state.uid is None:
    pg = st.navigation(
        [
            st.Page("discover_page.py"),
            st.Page("login_page.py"),
        ],
        position="top"
    )
else:
    pg = st.navigation(
        [
            st.Page("home_page.py"),
            st.Page("discover_page.py")
        ],
        position="top"
    )

pg.run()