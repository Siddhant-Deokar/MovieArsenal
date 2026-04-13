import streamlit as st

import pandas as pd

# importing recommend functions
from recommender import  collab_recommend ,content_based_recommend

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

if "collab_sample" not in st.session_state:
    st.session_state.collab_sample = None

if "content_sample" not in st.session_state:
    st.session_state.content_sample = None
    
    
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False


st.set_page_config(layout="wide")

@st.cache_resource
def load_popular_df( ):
    popular_df = pd.read_csv('data/processed/popular_movies.csv')
    
    return popular_df


popular_df =  load_popular_df()

user_id = st.session_state.get("uid")

num_movies = 7

collab_based = collab_recommend(user_id)

content_based = content_based_recommend(user_id)

if st.session_state.collab_sample is None:
    st.session_state.collab_sample = collab_based.sample(num_movies)

if st.session_state.content_sample is None:
    st.session_state.content_sample = content_based.sample(num_movies)


def print_row(df, title):
    st.subheader(title)

    cols = st.columns(num_movies) 
    
    for i,j in enumerate(cols):
        
        with j:
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
# --------------------Page Begin--------------------

# st.markdown("---")


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

st.header("Home Page")


if st.button("Refresh Recommendations"):
    st.session_state.collab_sample = collab_based.sample(num_movies)
    st.session_state.content_sample = content_based.sample(num_movies)
    st.session_state.selected_movie = None
    st.session_state.show_dialog = False

print_row(st.session_state.collab_sample, 'Similar users liked...')
st.divider()

print_row(st.session_state.content_sample, 'Based on what you liked...')
st.divider()


print_row(popular_df,'Popular Movies...')


if st.session_state.show_dialog:
    show_movie_details(st.session_state.selected_movie)
    st.session_state.show_dialog = False

