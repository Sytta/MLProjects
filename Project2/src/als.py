import numpy as np
import scipy
import scipy.io
import scipy.sparse as sp
from itertools import groupby
import pandas as pd
import os
from helpers import *
from baseline_helpers import user_habit_standardize, user_habit_standardize_recover

def read_txt(path):
    """read text file from path."""
    with open(path, "r") as f:
        return f.read().splitlines()


def load_data(path_dataset):
    """Load data in text format, one rating per line, as in the kaggle competition."""
    data = read_txt(path_dataset)[1:]
    return preprocess_data(data)


def preprocess_data(data):
    """preprocessing the text data, conversion to numerical array format."""
    def deal_line(line):
        pos, rating = line.split(',')
        row, col = pos.split("_")
        row = row.replace("r", "")
        col = col.replace("c", "")
        return int(row), int(col), float(rating)

    def statistics(data):
        row = set([line[0] for line in data])
        col = set([line[1] for line in data])
        return min(row), max(row), min(col), max(col)

    # parse each line
    data = [deal_line(line) for line in data]

    # do statistics on the dataset.
    min_row, max_row, min_col, max_col = statistics(data)
    print("number of users: {}, number of movies: {}".format(max_row, max_col))

    # build rating matrix.
    ratings = sp.lil_matrix((max_row, max_col))
    for row, col, rating in data:
        ratings[row - 1, col - 1] = rating
    return ratings


def group_by(data, index):
    """group list of list by a specific index."""
    sorted_data = sorted(data, key=lambda x: x[index])
    groupby_data = groupby(sorted_data, lambda x: x[index])
    return groupby_data


def build_index_groups(train):
    """build groups for nnz rows and cols."""
    # row : items; cols: users
    nz_row, nz_col = train.nonzero()
    nz_train = list(zip(nz_row, nz_col))

    grouped_nz_train_byrow = group_by(nz_train, index=0) # group by items 

    nz_row_colindices = [(g, np.array([v[1] for v in value])) # indices of all the users that rated item g
                         for g, value in grouped_nz_train_byrow]
    
#     print(nz_row_colindices)

    grouped_nz_train_bycol = group_by(nz_train, index=1) # group by users
    nz_col_rowindices = [(g, np.array([v[0] for v in value])) # indices of all the movies rated by user g
                         for g, value in grouped_nz_train_bycol]
    return nz_train, nz_row_colindices, nz_col_rowindices


def get_number_per(ratings):
    """plot the statistics result on raw rating data."""
    # do statistics.
    num_users_per_movie = np.array((ratings != 0).sum(axis=0)).flatten()
    num_movies_per_user = np.array((ratings != 0).sum(axis=1).T).flatten()
    return num_users_per_movie, num_movies_per_user

def split_data(ratings, num_users_per_movie, num_movies_per_user,
               min_num_ratings, p_test=0.1):
    """split the ratings to training data and test data.
    Args:
        min_num_ratings: 
            all movies and users we keep must have at least min_num_ratings per movie and per user. 
    """
#     # set seed
#     np.random.seed(988)
    
    # select movie and user based on the condition.
    valid_movies = np.where(num_users_per_movie >= min_num_ratings)[0]
    valid_users = np.where(num_movies_per_user >= min_num_ratings)[0]
    valid_ratings = ratings[valid_users, :][: , valid_movies]  
    
    # init
    num_rows, num_cols = valid_ratings.shape
    train = sp.lil_matrix((num_rows, num_cols))
    test = sp.lil_matrix((num_rows, num_cols))
    
    print("the shape of original ratings. (# of row, # of col): {}".format(
        ratings.shape))
    print("the shape of valid ratings. (# of row, # of col): {}".format(
        (num_rows, num_cols)))
    # get the nonzero entry index of rating matrix
    nz_users, nz_movies = valid_ratings.nonzero()
    
    # split the data
    for movie in set(nz_movies):
        # randomly select a subset of ratings
        row, col = valid_ratings[:, movie].nonzero()
        selects = np.random.choice(row, size=int(len(row) * p_test))
        residual = list(set(row) - set(selects))

        # add to train set
        train[residual, movie] = valid_ratings[residual, movie]
        if(p_test > 0):
            # add to test set
            test[selects, movie] = valid_ratings[selects, movie]
    
    
    print("Total number of nonzero elements in origial data:{v}".format(v=ratings.nnz))
    print("Total number of nonzero elements in train data:{v}".format(v=train.nnz))
    print("Total number of nonzero elements in test data:{v}".format(v=test.nnz))
    return valid_ratings, train, test

def init_MF(train, num_features,weight=1.0):
    """init the parameter for matrix factorization."""

    num_user,num_movie = train.shape
    # initial the feature matrix
    movie_features = weight * np.random.rand(num_features,num_movie)
    user_features = weight * np.random.rand(num_features,num_user)
    
    user_nnz = train.getnnz(axis=1)
    user_sum = train.sum(axis=1)

    return movie_features, user_features

def compute_error(data, movie_features, user_features, nz):
    """compute the loss (RMSE) of the prediction of nonzero elements."""
    # calculate rmse (we only consider nonzero entries.)
    mse = 0
    for row,col in nz:
        movie = movie_features[:,col]
        user = user_features[:,row]
        mse += ((data[row,col] - movie.T.dot(user))**2)

    rmse = np.sqrt(1.0*mse/len(nz))
    return rmse

def update_movie_feature(
        train, user_features, lambda_movie,
        nnz_users_per_movie, nz_movie_userindices):
    """update movie feature matrix."""
    """the best lambda is assumed to be nnz_users_per_movie[movie] * lambda_movie"""
    # update and return movie feature.
    num_movies = nnz_users_per_movie.shape[0]
    num_features = user_features.shape[0]
    lambda_I = lambda_movie * sp.eye(num_features)
    updated_movie_features = np.zeros((num_features,num_movies))
    
    # update the movie feature matrix one movie by one
    for movie,user in nz_movie_userindices:
        M = user_features[:,user]
        
        V = M @ train[user,movie]
        A = M @ M.T + nnz_users_per_movie[movie] * lambda_I
        Z_star = np.linalg.solve(A,V)
        updated_movie_features[:,movie] = np.copy(Z_star.T)
    return updated_movie_features

def update_user_feature(
        train, movie_features, lambda_user,
        nnz_movies_per_user, nz_user_movieindices):
    """update user feature matrix."""
    """the best lambda is assumed to be nnz_users_per_user[user] * lambda_user"""
    # update and return user feature.
    num_users = nnz_movies_per_user.shape[0]
    num_features = movie_features.shape[0]
    lambda_I = lambda_user * sp.eye(num_features)
    updated_user_features = np.zeros((num_features,num_users))
    
    # update the user feature matrix one user by one
    for user,movie in nz_user_movieindices:
        M = movie_features[:,movie]
        
        V = M @ train[user,movie].T
        A = M @ M.T + nnz_movies_per_user[user] * lambda_I
        W_star = np.linalg.solve(A,V)
        updated_user_features[:,user] = np.copy(W_star.T)
    return updated_user_features

def ALS(train,num_features,lambda_movie,lambda_user,max_weight=1.0,iterations=50):
    """Alternating Least Squares (ALS) algorithm."""
    # define parameters
    stop_criterion = 1e-5
    change = 1
    error_list = [0, 0]
    it = 0
 
    nz_row, nz_col = train.nonzero()
    nz_train = list(zip(nz_row, nz_col))
    

    # init ALS
    movie_features, user_features = init_MF(train, num_features,max_weight)
    
    # get the number of non-zero ratings for each movie and user
    nnz_users_per_movie,nnz_movies_per_user = train.getnnz(axis=0),train.getnnz(axis=1)
    
    # group the indices by row or column index
    _, nz_user_movieindices, nz_movie_userindices = build_index_groups(train)
    
    train_rmse = 0
    # start ALS
    while(it < iterations):
        movie_features = update_movie_feature(train, user_features, lambda_movie,
                            nnz_users_per_movie, nz_movie_userindices)
        
        user_features = update_user_feature(train, movie_features, lambda_user,
                            nnz_movies_per_user, nz_user_movieindices)
        
        train_rmse = compute_error(train,movie_features,user_features,nz_train)
#         print("ALS training RMSE : {err}".format(err=train_rmse))
        error_list.append(train_rmse)
        change = np.fabs(error_list[-1] - error_list[-2])
        # if change is small enough then stop
        if (change < stop_criterion):
            print("Converge!")
            break;
        it += 1
        
    print("ALS Final training RMSE : {err}".format(err=train_rmse))
    
    return user_features,movie_features

def cv_ALS_random_search(train,test=None,seed=988):
    """random search cross-validation to tune hyper-parameters"""
    
    # randomly generate candidate parameters from appropriate range
    movies_range = np.linspace(0.01,1,num=100)
    user_range = np.linspace(0.01,1,num=100)
    features_num_range = np.linspace(1,60,num=60,dtype=np.int32)
    weight_range = np.linspace(1.0,3.0,num=60)
    # randomly select 60 parameters to tune 
    # because 60 iterations is enough to reach 0.95 probability to find the optimal
    lambda_movies = np.random.choice(movies_range,60)
    lambda_users = np.random.choice(user_range,60)
    nb_features = np.random.choice(features_num_range,60)
    weights = np.random.choice(weight_range,60)
    
    # for test
#     lambda_movies = [0.01]
#     lambda_users = [0.2]
#     nb_features = [20]
#     weights = [1.0]
    
    best_weight = -1
    best_lambda_user = -1
    best_lambda_movie = -1
    best_num_feature = -1
    best_rmse = 100
    
    k_fold = 5
    
    newpath = r'./data' 
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    # initial train data and test data from training dataset for 5-fold cross-validation
    train_tr_list, test_tr_list = split_for_cv(train,p_test=0.2)
    for num_features,weight,lambda_movie,lambda_user in zip(nb_features,weights,lambda_movies,lambda_users):
        rmse_list = []
        for train_tr,test_tr in zip(train_tr_list, test_tr_list): # 5-fold cv
            user_features,movie_features = ALS(train_tr,num_features,lambda_movie,lambda_user,weight)
            nz_row, nz_col = test_tr.nonzero()
            nz_test = list(zip(nz_row, nz_col))
            test_tr_rmse = compute_error(test_tr, movie_features, user_features, nz_test)
            print("RMSE on test data after ALS: {}.".format(test_tr_rmse))  
#             print("test RMSE: {te_rmse}" .format(te_rmse=test_tr_rmse))
            rmse_list.append(test_tr_rmse)
        test_rmse = np.mean(rmse_list)
        # save best parameters
        if(test_rmse < best_rmse):
            best_rmse = test_rmse
            bset_lambda_user = lambda_user
            best_lambda_movie = lambda_movie
            best_weight = weight
            best_num_feature = num_features
            best_rmse = test_rmse
            print("CHANGE=====>best rmse: {},lambda_user :{},lambda_movie:{},weight:{},num_feature:{}"\
                  .format(best_rmse,bset_lambda_user,best_lambda_movie,best_weight,best_num_feature))
            
    print("=======>>>> FINAL: BEST RMSE: {},lambda_user :{},lambda_movie:{},weight:{},num_feature:{}"\
                              .format(best_rmse,bset_lambda_user,best_lambda_movie,best_weight,best_num_feature))
    
    best_param = np.array([best_num_feature,best_weight,best_lambda_movie,bset_lambda_user])
#     np.save("best_param_random_search.npy", best_param)
    return best_num_feature,best_weight,best_lambda_movie,bset_lambda_user

def split_for_cv(train,p_test=0.2,k_fold=5):
    """split training data into test data and train data for cv randomly"""
    # init
    num_rows, num_cols = train.shape
    nz_users, nz_movies = train.nonzero()
    train_tr_list=[]
    test_tr_list = []
    # for test
#     k_fold = 1
    # split the data
    for k in range(k_fold):
        train_tr = sp.lil_matrix((num_rows, num_cols))
        test_tr = sp.lil_matrix((num_rows, num_cols))
        for movie in set(nz_movies):
            # randomly select a subset of ratings
            row, col = train[:, movie].nonzero()
            selects = np.random.choice(row, size=int(len(row) * p_test))
            residual = list(set(row) - set(selects))

            # add to train set
            train_tr[residual, movie] = train[residual, movie]

            # add to test set
            test_tr[selects, movie] = train[selects, movie]
            
        train_tr_list.append(train_tr)
        test_tr_list.append(test_tr)
        
    return train_tr_list, test_tr_list

def predict_ALS(num_features=None,lambda_movie=None,lambda_user=None,weight=None,load_File=None):
    """just simply use to predict by ALS"""
    seed = 988
    train_dataset = "./data/data_train.csv"
    ratings = load_data(train_dataset)
    
    # set seed
    np.random.seed(seed)
    # split data
    num_users_per_movie,num_movies_per_user = get_number_per(ratings)
    valid_ratings, train, _= split_data(
    ratings, num_users_per_movie, num_movies_per_user, min_num_ratings=0, p_test=0)
    
    if(load_File==1):
        best_param = np.load("best_param_random_search.npy")
        num_features = best_param[0]
        weight = best_param[1]
        lambda_movie = best_param[2]
        lambda_user = best_param[3]
#     else:
#         num_features = 20
#         weight = 2.18644068
#         lambda_movie = 0.02
#         lambda_user = 0.47
    # ALS
    user_features,movie_features = ALS(train,num_features,lambda_movie,lambda_user,weight)
    # predict
    predict_labels = user_features.T @ movie_features
    predict = np.asarray(predict_labels.T)
    # change the matrix into dataframe
    movie_user_predict = pd.DataFrame(data=predict)
    movie_user_predict.reset_index(inplace=True)
    movie_user_predict.rename(columns={"index":"Movie"},inplace=True)
    movie_user_predict_melt = pd.melt(movie_user_predict,id_vars=["Movie"],var_name="User",value_name ="Rating")
    movie_user_predict_melt["Movie"] = movie_user_predict_melt["Movie"].values +1
    movie_user_predict_melt["User"] = movie_user_predict_melt["User"].values +1
    
    # match ID in samplesubmission
    sample = pd.read_csv("./data/sampleSubmission.csv")
    movie_user_predict_melt['Id'] = movie_user_predict_melt.apply(lambda x: 'r{}_c{}'.format(int(x.User), int(x.Movie)), axis=1)
    prediction = movie_user_predict_melt[movie_user_predict_melt.Id.isin(sample.Id.values)]
    prediction = prediction[["User","Movie","Rating"]]
    
    return prediction


def run_cross_validation(intest=0,seed=988):
    """Function to run the cross-validation"""
    train_dataset = "./data/data_train.csv"
    ratings = load_data(train_dataset)
    
    # set seed
    np.random.seed(seed)
    # split data
    num_users_per_movie,num_movies_per_user = get_number_per(ratings)
    valid_ratings, train, test = split_data(
    ratings, num_users_per_movie, num_movies_per_user, min_num_ratings=0, p_test=0.2)
    if(intest ==1):
        num_features = 20
        weight = 1.0
        lambda_movie = 0.2
        lambda_user = 0.02
    else:
        num_features,weight,lambda_movie,lambda_user = cv_ALS_random_search(train,test)
    # ALS    
    user_features,movie_features = ALS(train,num_features,lambda_movie,lambda_user,weight)
    nz_row, nz_col = test.nonzero()
    nz_test = list(zip(nz_row, nz_col))
    test_rmse = compute_error(test, movie_features, user_features, nz_test)
    print("RMSE on test data after ALS: {}.".format(test_rmse))


def als_algo(train_df,test_df, model):
    """running ALS for blending"""
    # get users and movies from train_df and test_df
    train_users = train_df['User'].values
    train_movies = train_df['Movie'].values
    # get the number of user and movie to decide the shape of matrix
    num_rows,num_cols = len(train_df['User'].value_counts()),len(train_df['Movie'].value_counts())
    train = sp.lil_matrix((num_rows, num_cols))
    test = sp.lil_matrix((num_rows, num_cols))
    # set value in training data matrix according to training dataframe 
    for row,col in zip(train_users,train_movies):
        train[row-1,col-1] = train_df.loc[(train_df['User']==row) &(train_df['Movie']==col),'Rating'].values[0]
    
    # use best parameters from tuning
    num_features = 20
    weight = 2.18644068
    lambda_movie = 0.02
    lambda_user = 0.47
    # ALS
    user_features,movie_features = ALS(train,num_features,lambda_movie,lambda_user,weight)
    # predict
    predict_labels = user_features.T @ movie_features
    predict = np.asarray(predict_labels.T)
    # change data matrix into dataframe
    movie_user_predict = pd.DataFrame(data=predict)
    movie_user_predict.reset_index(inplace=True)
    movie_user_predict.rename(columns={"index":"Movie"},inplace=True)
    movie_user_predict_melt = pd.melt(movie_user_predict,id_vars=["Movie"],var_name="User",value_name ="Rating")
    movie_user_predict_melt["Movie"] = movie_user_predict_melt["Movie"].values +1
    movie_user_predict_melt["User"] = movie_user_predict_melt["User"].values +1
    
    # match test_df
    test_copy = test_df.copy()
    test_copy['Id'] = test_copy.apply(lambda x: 'r{}_c{}'.format(int(x.User), int(x.Movie)), axis=1)
    movie_user_predict_melt['Id'] = movie_user_predict_melt.apply(lambda x: 'r{}_c{}'.format(int(x.User), int(x.Movie)), axis=1)
    prediction = movie_user_predict_melt[movie_user_predict_melt.Id.isin(test_copy.Id.values)]
    prediction = prediction[["User","Movie","Rating"]]
    print("[als_algo] prediction: {}".format(prediction.head()))
    return prediction

def als_algo_user_std(train_df,test_df, model):
    """run ALS with user habit standardization"""
    # standardize
    train_user_std = user_habit_standardize(train_df)
    pred = als_algo(train_user_std, test_df, model)
    # recover 
    pred_recovered = user_habit_standardize_recover(train_df, pred)
    
    return pred_recovered

