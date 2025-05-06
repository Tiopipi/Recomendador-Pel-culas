import numpy as np
cimport numpy as np
from libc.math cimport sqrt

ctypedef np.float64_t DTYPE_t

def calculate_similarity_for_user_pair_cy(tuple args):
    """Versión Cython optimizada para calcular la correlación de Pearson entre usuarios"""
    user1, user2, user1_ratings, user2_ratings, min_peliculas = args

    cdef:
        set common_movies
        int n_common
        np.ndarray[DTYPE_t, ndim=1] ratings1
        np.ndarray[DTYPE_t, ndim=1] ratings2
        double sum1 = 0.0
        double sum2 = 0.0
        double mean1, mean2
        double numerator = 0.0
        double diff1, diff2
        double denom1 = 0.0
        double denom2 = 0.0
        double pearson = 0.0
        list movie_ids = []
        object movie_id
        int i

    common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())
    n_common = len(common_movies)

    if n_common >= min_peliculas:
        movie_ids = list(common_movies)
        ratings1 = np.zeros(n_common, dtype=np.float64)
        ratings2 = np.zeros(n_common, dtype=np.float64)

        for i in range(n_common):
            movie_id = movie_ids[i]
            ratings1[i] = user1_ratings[movie_id]
            ratings2[i] = user2_ratings[movie_id]

        for i in range(n_common):
            sum1 += ratings1[i]
            sum2 += ratings2[i]

        mean1 = sum1 / n_common
        mean2 = sum2 / n_common

        for i in range(n_common):
            diff1 = ratings1[i] - mean1
            diff2 = ratings2[i] - mean2
            numerator += diff1 * diff2
            denom1 += diff1 * diff1
            denom2 += diff2 * diff2

        if denom1 > 0 and denom2 > 0:
            pearson = numerator / (sqrt(denom1) * sqrt(denom2))
            return (user1, user2, pearson)

    return None
