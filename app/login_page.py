# LOGIN PAGE                
import streamlit as st
import pickle
import time


st.set_page_config(layout="wide")


@st.cache_resource
def load_user_id_map():
    
    with open('models/artifacts/mappings/full_user_id_map.pkl', 'rb') as file:
        user_id_map = pickle.load(file)
        file.close()
    return user_id_map

user_id_map = load_user_id_map()


def stream_text(text):
            for char in text:
                yield char
                time.sleep(0.02)  # typing speed




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


col1, col2, col3 = st.columns([1, 2, 1])
if st.session_state.uid is None:
    with col2:
        st.title("Login")
        st.caption("You can simulate as a user to visit home page")
        
        with st.form("login_form", clear_on_submit=False):
            uid = st.text_input("Enter User Id")
            submitted = st.form_submit_button("Submit")

            if submitted:
                try:
                    _ = user_id_map[int(uid)]
                    
                    st.session_state.uid = int(uid)
                    st.rerun()
                except Exception:
                    st.error("User id doesn't exist")
                    
        # st.write("You can also check out the Discover page without logging in",text_alignment='center')
        # st.write_stream("You can also check out the Discover page without logging in")
        
        

        

        st.write_stream(stream_text(
            "You can also check out the Discover page without logging in."
        ))
  
        


    