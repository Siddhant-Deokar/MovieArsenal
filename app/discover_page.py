import streamlit as st
import pandas as pd
from recommender import cold_start_recommender

# st.set_page_config(layout="wide")

# -------- STATE --------
if "onboarding_recs" not in st.session_state:
    st.session_state.onboarding_recs = None

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False


# -------- LOAD --------
@st.cache_resource
def load_movie_options():
    df = pd.read_csv("data/processed/display_movie_data.csv")
    movie_options = df['title'].unique().tolist()
    return df, movie_options


# -------- UI --------


df, movie_options = load_movie_options()


# CSS
st.markdown("""
<style>
div[data-baseweb="select"] > div {
    min-height: 45px !important;
    max-height: 45px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- CENTER CONTENT ----------

st.html(f"""
<div style='
    display: flex; 
    justify-content: space-between; 
    align-items: center;
    margin-bottom: 14px;
'>

    <div style='
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 0.5px;
    '>
        MovieArsenal
    </div>

    <div style='
        font-size: 16px;
        opacity: 0.8;
    '>
        <b>User:</b> {st.session_state.uid if st.session_state.uid else "Guest"}
    </div>

</div>
""")

st.markdown("<hr style='margin: 6px 0;'>", unsafe_allow_html=True)

top_space, main, bottom_space = st.columns([1, 2, 1])

with main:
    st.header("Discover Movies")
    st.caption("Pick a few movies to get recommendations")

    selected = st.multiselect("", options=movie_options)
    num_movies = st.number_input("Number of movies", min_value=1, value=5)

    if st.button("Get Recommendations", width='stretch'):
        if len(selected) < 5:
            st.warning("Select at least 5 movies")
        else:
            st.session_state.onboarding_recs = cold_start_recommender(selected, num_movies)
            st.session_state.selected_movie = None
        
        
# -------- DISPLAY --------
def print_row(df):
    # cols = st.columns(5)
    cols = st.columns([1,1,1,1,1], gap="small")
    for i in range(len(df)):
        with cols[i]:
            # st.image(df.iloc[i,10])
            st.image(df.iloc[i,10], width=200,)
            st.write(df.iloc[i,1])

            if st.button("View", key=f"view_{df.iloc[i]['MovieID']}"):
                st.session_state.selected_movie = df.iloc[i]
                st.session_state.show_dialog = True


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


if st.session_state.onboarding_recs is not None:
    movies = st.session_state.onboarding_recs
    
    if movies is not None:
        st.subheader("Recommendations")
    for i in range(0, len(movies), 5):
        print_row(movies.iloc[i:i+5])


if st.session_state.show_dialog:
    show_movie_details(st.session_state.selected_movie)
    st.session_state.show_dialog = False