import pandas as pd
import streamlit as st
import pickle
import requests

# other_api_key = 8392bef86d527087d70782c7b88b2bf9

### contend based fitering:

# Lấy ra title, vote_average, poster_path, imdb_id khi truyền vào movie_id
def fetch_poster_vote_title(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=020b311fe0559698373a16008dc6a672&language=en-US'.format(movie_id))
    data = response.json()
    title = ''
    vote_average = 0
    poster_path = "poster_not_found.png"
    imdb_id = ''

    if 'poster_path' in data and data['poster_path'] is not None:
        poster_path = "https://image.tmdb.org/t/p/w500/" + data['poster_path']

    if 'title' in data and data['title'] is not None:
        title = data['title']

    if 'vote_average' in data and data['vote_average'] is not None:
        vote_average = data['vote_average']

    if 'imdb_id' in data and data['imdb_id'] is not None:
        imdb_id = data['imdb_id']

    return title, vote_average, poster_path, imdb_id

# Nhận tile movie đầu ra là list các movie_title gợi ý và poster tương ứng:
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    for x in movies_list:
        movie_id = movies.iloc[x[0]].movie_id
        recommended_movies.append(movies.iloc[x[0]].title)
        if fetch_poster_vote_title(movie_id)[2] is None:
            recommended_movies_posters.append("poster_not_found.png")
        else:
            recommended_movies_posters.append(fetch_poster_vote_title(movie_id)[2])

    return recommended_movies, recommended_movies_posters


movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity_v2.pkl', 'rb'))


### collaborative filtering:

movies_metadata = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')

# xuất ra các thông tin liên quan đến 1 user:
def get_movie_info(user_id):
    movies_df = pd.read_csv('movies.csv', low_memory=False)
    movies_df['title'] = movies_df['title'].str.replace(r'\(\d{4}\)', '')
    movies_df['title'] = movies_df['title'].str.strip()

    ratings_df = pd.read_csv('ratings.csv', low_memory=False)

    links_df = pd.read_csv('links.csv', low_memory=False)

    movies_metadata_df = pd.read_csv('movies_metadata.csv', low_memory=False)
    movies_metadata_df = movies_metadata_df.loc[:, ['id', 'imdb_id', 'title']]


    movie_new_df = pd.merge(movies_df, movies_metadata_df, on='title')

    if user_id not in ratings_df['userId'].unique():
        return None

    user_ratings = ratings_df[ratings_df['userId'] == user_id]

    user_movie_ratings = pd.merge(movie_new_df, user_ratings, on='movieId')

    user_movie_ratings_links = pd.merge(user_movie_ratings, links_df, on='movieId')

    movie_info = user_movie_ratings_links[['movieId', 'title', 'rating', 'imdb_id', 'id']].values.tolist()
    return movie_info[:20]

def user_get_top(user_id, user_final_ratings_matrix):
    links_df = pd.read_csv('links.csv', low_memory=False)
    movies_df = pd.read_csv('movies.csv', low_memory=False)

    movies_links_df = pd.merge(movies_df, links_df, on='movieId')

    top_movieIds = user_final_ratings_matrix.iloc[user_id].sort_values(ascending=False)[0:20].index

    top_tmdbId = movies_links_df.loc[movies_links_df['movieId'].isin(top_movieIds), 'tmdbId']

    movies_links_df.head()
    top_tmdbId = top_tmdbId.tolist()

    top_tmdbId = list(map(int, top_tmdbId))
    return top_tmdbId

###streamlit:
st.set_page_config(
    page_title="Movie App",
    page_icon="👋",
)


with st.sidebar:
    st.sidebar.title("Dashboard")
    add_userID = int(st.number_input('🙍‍♂️Nhập User Id:'))
    with st.form('form1'):
        if add_userID <= 6471:
            add_password = st.text_input('🔐 Nhập mật khẩu:')
        st.form_submit_button('Enter')

info_user = get_movie_info(add_userID)

add_selectbox = st.sidebar.selectbox(
    "Liên hệ với chúng tôi",
    ("📧 Email: movierecomm@hus.edu.vn", "☎️ Số điện thoại: 1393791813", "📍 Địa chỉ: 334 Nguyễn Trãi Thanh Xuân Hà Nội")
)

st.title('Hệ thống đề xuất phim 🎞️')

selected_movie_name = st.selectbox(
    'Hãy lựa chọn bộ phim mà bạn thích hoặc đã xem:',
    movies['title'].values
)

if st.button('Gợi ý'):
    st.write("Có thể bạn cũng thích:")
    names, posters = recommend(selected_movie_name)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.text(names[0])
        st.image(posters[0])
    with col2:
        st.text(names[1])
        st.image(posters[1])
    with col3:
        st.text(names[2])
        st.image(posters[2])
    with col4:
        st.text(names[3])
        st.image(posters[3])
    with col5:
        st.text(names[4])
        st.image(posters[4])

if info_user is not None:

    with st.expander("Danh sách phim bạn đã đánh giá"):
        for i in info_user:
            col1, col2, col3, col4 = st.columns(4)

            link = "https://www.imdb.com/title/" + i[3]
            with col1:
                st.image(fetch_poster_vote_title((i[4]))[2], caption='', width=100)

            with col2:
                st.markdown(f'**Tên phim**: {i[1]}')
                st.markdown(f'**Đã đánh giá**: {i[2]} ⭐')
                st.markdown(f'[Đến trang imdb.com]({link})')


    user_final_ratings_matrix = pickle.load(open('user_final_ratings.pkl', 'rb'))
    top_tmdbId = user_get_top(add_userID, user_final_ratings_matrix)
    list_recomm = []
    for tmdbId in top_tmdbId:
        list_recomm.append(fetch_poster_vote_title(tmdbId))

    st.subheader("Các phim đề xuất cho User {}:".format(add_userID))
    for r in list_recomm:
        col1, col2 = st.columns(2)
        title = r[0]
        vote_average = round(r[1], 1)
        poster_path = r[2]
        link = "https://www.imdb.com/title/" + r[3]


        with col1:
            st.image(poster_path, caption='', width=150)
        with col2:
            st.markdown(f'**Tên phim**: {title}')
            st.markdown(f'**Đánh giá trung bình**: {vote_average}/10')
            st.markdown(f'[Đến trang imdb.com]({link})')














