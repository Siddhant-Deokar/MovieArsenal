import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from collections import Counter


@st.cache_resource
def load_resources():
    ratings = pd.read_csv(
        "data/raw/MovieLens 1M/ratings.dat",
        sep="::",
        engine="python",
        encoding="latin-1",
        names = ['UserID','MovieID','Rating','Timestamp']
    )

    df = pd.read_csv('data/processed/display_movie_data.csv')

    try:
        df = df.drop(columns = 'Unnamed: 0')
    except:
        pass

    # Importing all the necessary things

    model = tf.keras.models.load_model('models/tf/recommender_model_cf_final.keras')

    user_emb_matrix   = model.get_layer('user_emb').get_weights()[0]
    movie_emb_matrix  = model.get_layer('movie_emb').get_weights()[0]
    user_bias_matrix  = model.get_layer('user_bias').get_weights()[0]
    movie_bias_matrix = model.get_layer('movie_bias').get_weights()[0]

  

    global_mean = np.load('models/artifacts/stats/global_mean.npy')
    global_std = np.load('models/artifacts/stats/global_std.npy')


    with open('models/artifacts/mappings/full_user_id_map.pkl', 'rb') as file:
        user_id_map = pickle.load(file)
        file.close()

    with open('models/artifacts/mappings/full_movie_id_map.pkl', 'rb') as file:
        movie_id_map = pickle.load(file)
        file.close()

    idx2movie = {v:k for k,v in movie_id_map.items()}


    ratings['user_idx']  = ratings['UserID'].map(user_id_map)
    ratings['movie_idx'] = ratings['MovieID'].map(movie_id_map)

    movie_rating_counts = ratings.groupby('movie_idx')['Rating'].count()


    # Content based recommender imports
    tfidf_matrix = sparse.load_npz('models/artifacts/matrices/tfidf_matrix.npz')


    with open('models/artifacts/mappings/cb_movie_to_id.pkl', 'rb') as file:
        cb_movie_to_id = pickle.load(file)
        file.close()
        
    with open('models/artifacts/mappings/cb_id_to_movie.pkl', 'rb') as file:
        cb_id_to_movie = pickle.load(file)
        file.close()
        
    
    
    return (
        # Collaborative filtering function imports
        ratings, df, model,
        user_emb_matrix, movie_emb_matrix, user_bias_matrix, movie_bias_matrix,
        global_mean, global_std,
        user_id_map, movie_id_map, idx2movie, movie_rating_counts,
        
        # Content Based function imports
        tfidf_matrix, cb_movie_to_id, cb_id_to_movie,
    ) 


(ratings, df, model,
    user_emb_matrix, movie_emb_matrix, user_bias_matrix, movie_bias_matrix,
    global_mean, global_std,
    user_id_map, movie_id_map, idx2movie, movie_rating_counts,
    tfidf_matrix, cb_movie_to_id, cb_id_to_movie
        
        ) = load_resources()



# ---------------------------------------Collaborative Filtering---------------------------------------
@st.cache_data     
def collab_recommend(user_id, num_movies=25, min_num_rating= 50, ):
    
    """
    Recommends movies using collaborative filtering.
    Filters to movies with at least min_num_rating ratings.
    Excludes movies the user has already watched(rated in this case).
    """
    
    popular_movie_idxs  = movie_rating_counts[movie_rating_counts >= min_num_rating].index.values

    # Tensorflow embedding layers expect int32
    popular_movie_arr = popular_movie_idxs.astype('int32')
    
    
    ## Getting User Idx to match with user's embedding's index
    user_idx = user_id_map[user_id]
    
    # Exclude already watched movies
    # Using a set to speed up checks. eg:    if x in set 
    watched_movies = set(ratings[ratings['UserID'] == user_id]['MovieID'].values)
    
    
    # Manual matrix multiply — much faster than model.predict
    predictions = (( movie_emb_matrix[popular_movie_arr] @ user_emb_matrix[user_idx] ) + movie_bias_matrix[popular_movie_arr].flatten() + user_bias_matrix[user_idx].flatten())
    
    # Convert z-score back to real ratings
    predictions = (predictions * global_std ) + global_mean
 
    
    # sorting based on rating
    predictions_with_indexes = sorted(
        zip(popular_movie_arr, predictions),
        key=lambda x: x[1],
        reverse=True
    )
    
    # extracting idx 
    recommend_movie_idx = [idx for idx, _ in predictions_with_indexes]

    # fetching actual movie_id 
    recommend_movie_ids = [idx2movie[idx] for idx in recommend_movie_idx]
    
    # removing the already watched movies
    recommend_movie_ids = [i for i in recommend_movie_ids if i not in watched_movies] 
    
    return df.loc[df['MovieID'].isin(recommend_movie_ids),:].head(num_movies)
   
   
   
   
# Content Based Recommender
@st.cache_data     
def content_based_recommend(user_id,num_movies = 20):
    
    """
    Recommends movies using Content Based Recommendation.
    Recommends based on user's top rated movies
    Builds a taste vector by averaging TF-IDF vectors of favourite movies.
    Excludes movies the user has already watched(rated in this case).
    """
    
    # Selecting top rated movies by the user
    user_df = ratings[ratings['UserID'] == user_id].sort_values(by='Rating',ascending = False ).copy()
    
    min_rating = 5
    
    fav_movie_ids = None
    
    # extracting the movie history 
    movie_history = user_df['MovieID'].values
    movie_history = [cb_movie_to_id[i] for i in movie_history if i in cb_movie_to_id ]

    while min_rating >= 3:

        no_of_movies = user_df[ user_df['Rating'] >= min_rating ].shape[0]

        if no_of_movies < 20:
            min_rating -=1
            continue
        
        fav_movie_ids = user_df[ user_df['Rating'] >= min_rating ].head(20)['MovieID'].values.tolist()
        break

    # if they haven't rated much movies above 3, we just return top 20 no matter rating they gave
    if fav_movie_ids is None:
        fav_movie_ids = user_df.head(20)['MovieID'].values.tolist()
        
            
    # check whether the movie exists in the map (as we did drop some old movies with incomplete data, which wold rarely be a problem)        
    fav_movie_idx = [cb_movie_to_id[i] for i in fav_movie_ids if i in cb_movie_to_id] 
        
    fav_vectors = tfidf_matrix[fav_movie_idx]
    
    mean_vector = fav_vectors.mean(axis=0)
    mean_vector = np.asarray(mean_vector)
    # cosine similarity expects a 2d array, our mean_vector is current 1d -> [1,2,3,..]
    mean_vector = mean_vector.reshape(1,-1) # converting [1,2] -> [[1,2]] 

    # 2d vector
    similiaritiess = cosine_similarity(mean_vector, tfidf_matrix)

    similiaritiess = similiaritiess.flatten()

    # sorts the index. like argmin() return id of min
    most_similar_movies = similiaritiess.argsort()


    # Remove already watched 
    most_similar_movies = most_similar_movies[~np.isin(most_similar_movies, movie_history)]

    # Descending order
    recommend_movies_idx = most_similar_movies[::-1][:num_movies]
    

    # Finding most similar movies to the recommended movies, for personalised Section labels
   
   # vectors
    recommended_vectors = tfidf_matrix[recommend_movies_idx]
    
    # similarity (num_movies x 20)
    sim_matrix = cosine_similarity(recommended_vectors, fav_vectors)
    
    top_movie_idx_per_recommended_movie = np.argmax(sim_matrix,axis = 1)
    
    # map to TF-IDF indices
    top1_fav_idx = [fav_movie_idx[i] for i in top_movie_idx_per_recommended_movie]
    
    top1_movie_ids = [
    cb_id_to_movie[int(i)] for i in top1_fav_idx if int(i) in cb_id_to_movie
    ]
    
    # returns a list of tuple, id with its count [(id, count(id)), (id, count(id))]
    top_movies = Counter(top1_movie_ids).most_common(2)
    top_movies = [movie_id for movie_id,_ in top_movies]
    
    try:
        # if both id exists
        top_movies = df.set_index('MovieID').loc[top_movies,'title'].values
    
    except:
        top_movies = df[df['MovieID']].isin(top_movies)['title'].values

    if len(top_movies)>1:
        top_movies = ' and '.join(top_movies)
        
    else:
        top_movies = top_movies[0]
    
    # converting idx to MovieId
    recommend_movies_id = [ cb_id_to_movie[int(i)] for i in recommend_movies_idx if int(i) in cb_id_to_movie][:num_movies]

    return  top_movies, df.loc[df['MovieID'].isin(recommend_movies_id),:]


# ── Cold Start (Discover page — no login needed) ─────────────────────────────  
@st.cache_data
def cold_start_recommender(selected_movies, num_movies=5):
    """
    Cold-start recommender for users without prior ratings.
    Takes a list of selected movie titles, constructs a user preference
    vector by averaging their TF-IDF representations, and recommends
    similar movies using cosine similarity.

    """
    
    movie_ids  = df[df['title'].isin(selected_movies)]['MovieID'].values
        
    movie_idxs = [cb_movie_to_id[i] for i in movie_ids if i in cb_movie_to_id]
    
    if not movie_idxs:
        return None
    
    # cosine similarity expects a 2d array, our mean_vector is current 1d -> [1,2,3,..]
    
    mean_vector = tfidf_matrix[movie_idxs].mean(axis=0) # converting [1,2] -> [[1,2]] 
    mean_vector = np.asarray(mean_vector).reshape(1,-1)


    # 2d vector
    similiaritiess = cosine_similarity(mean_vector, tfidf_matrix).flatten()

    # sorts the index. like argmin() return id of min
    most_similar_movies = similiaritiess.argsort()
    
    # Remove selected movies
    most_similar_movies = most_similar_movies[~np.isin(most_similar_movies, movie_idxs)]

    recommend_movies = most_similar_movies[::-1]
    
    
    # converting idx to MovieId
    recommend_movies = [ cb_id_to_movie[int(i)] for i in recommend_movies if int(i) in cb_id_to_movie][:num_movies]

    return df.loc[df['MovieID'].isin(recommend_movies),:]
    
    
    
    
    
    







        

