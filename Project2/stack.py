from helpers import *
from baseline import *
from baseline_helpers import *
from surprise_helpers import *
from spotlight_helpers import *
from pyfm_helpers import *
from als import *
from MFRR import *
import scipy.optimize as sco

from os import listdir
from os.path import isfile, join
import shutil

def load_models():
    print("Loading models...")
    models_dict = dict(
        # Baseline parameters: (train, test)
        baseline = dict(
            global_mean = baseline_global_mean,
            global_median = baseline_global_median,
            user_mean = baseline_user_mean,
            user_median = baseline_user_median,
            movie_mean = baseline_movie_mean,
            movie_median = baseline_movie_median,
            movie_mean_user_std = movie_mean_user_standardize,
            movie_median_user_std = movie_median_user_standardize,
            movie_mean_user_habit_std = movie_mean_user_habit_standardize,
            movie_median_user_habit_std = movie_median_user_habit_standardize,
            movie_mean_user_habit = movie_mean_user_habit,
            movie_median_user_habit = movie_median_user_habit,
        ),
        
#         surprise
        surprise = dict(
            surprise_svd = SVD(n_factors=50, n_epochs=200, lr_bu=1e-9 , lr_qi=1e-5, reg_all=0.01),
#             surprise_svd_pp = SVDpp(n_factors=50, n_epochs=200, lr_bu=1e-9 , lr_qi=1e-5, reg_all=0.01),
            surprise_knn = KNNBaseline(k=100, sim_options={'name': 'pearson_baseline', 'user_based': False}),
        ),
        surprise_algo_user_std = dict(
            surprise_svd_user_std = SVD(n_factors=50, n_epochs=200, lr_bu=1e-9 , lr_qi=1e-5, reg_all=0.01),
#             surprise_svd_pp = SVDpp(n_factors=50, n_epochs=200, lr_bu=1e-9 , lr_qi=1e-5, reg_all=0.01),
            surprise_knn_user_std = KNNBaseline(k=100, sim_options={'name': 'pearson_baseline', 'user_based': False}),
        ),
        
#         spotlight
        spotlight = dict(
            spotlight=ExplicitFactorizationModel(loss='regression',
                                   embedding_dim=150,  # latent dimensionality
                                   n_iter=50,  # number of epochs of training
                                   batch_size=256,  # minibatch size
                                   l2=1e-5,  # strength of L2 regularization
                                   learning_rate=0.0001,
                                   use_cuda=torch.cuda.is_available()),
        ),

        spotlight_user_std = dict(
            spotlight_user_std=ExplicitFactorizationModel(loss='regression',
                                   embedding_dim=150,  # latent dimensionality
                                   n_iter=50,  # number of epochs of training
                                   batch_size=256,  # minibatch size
                                   l2=1e-5,  # strength of L2 regularization
                                   learning_rate=0.0001,
                                   use_cuda=torch.cuda.is_available()),
        ),
        
        # als
        als = dict(
            als= None
        ),
        
        als_user_std = dict(
            als_user_std = None
        ),
        
        # pyfm
        pyfm = dict(
            pyfm=pylibfm.FM(num_factors=20, num_iter=200, verbose=True, 
                          task="regression", initial_learning_rate=0.001, 
                          learning_rate_schedule="optimal")
        ),
        
        pyfm_user_std = dict(
            pyfm_user_std = pylibfm.FM(num_factors=20, num_iter=200, verbose=True, 
                          task="regression", initial_learning_rate=0.001, 
                          learning_rate_schedule="optimal")
        ),
        
        # MFRR
        mfrr = dict(
            mfrr= None
        ),
        
        mfrr_user_std = dict(
            mfrr_user_std = None
        )
    )
    
    model_msg = "{} model families loaded:\n ".format(len(list(models_dict.keys())))
    for i in list(models_dict.keys()):
        model_msg = model_msg + "{}; ".format(i)
    print(model_msg)
    return models_dict
   
    
def load_algos():
    algo_dict = dict(
        baseline = baseline_algo, # baseline_algo(train, test, model)
        surprise = surprise_algo, # surprise_algo(train, test, algo, verbose=True, training=False)
        surprise_user_std = surprise_algo_user_std,
        spotlight = spotlight_algo, # spotlight_algo(train, test, model, verbose=True)
        spotlight_user_std = spotlight_algo_user_std, # spotlight_algo(train, test, model, verbose=True)
        pyfm = pyfm_algo,
        pyfm_user_std = pyfm_algo_user_std, 
        mfrr = mf_rr_algo,  # mf_rr_algo(train, test, model)
        mfrr_user_std = mf_rr_algo_user_std,  # mf_rr_algo(train, test, model)
        als = als_algo,
        als_user_std = als_algo_user_std,
    )
    return algo_dict

# def predict_and_save(saving_folder, training = True):
#     # create folder 
#     if os.path.exists(saving_folder):
#         shutil.rmtree(saving_folder)
    
#     os.makedirs(saving_folder)
    
#     # load csv
#     train_df = load_dataset(train_dataset, min_num_ratings = 0)
#     test_df = load_dataset(test_dataset, min_num_ratings = 0)
    
#     # Split training to blend
#     if training:
#         print("Splitting data for training...")
#         train = train_df.copy()
#         train_df, test_df = split_dataset(train_df, p_test=0.5, min_num_ratings = 0)
#         # folds_dict = define_folds(train_df, 5) - FOR FOLDS?
    
#     # dictionary of the predictions
#     predictions = dict()
        
#     # load models
#     models_dict = load_models()
#     # load algos
#     algo_dict = load_algos()
#     t = Timer()
#     t.start()
#     for model_family_name, model_family in models_dict.items():
#         algo = algo_dict[model_family_name]
#         print("Predicting using algo: {}, model: {}...".format(algo, model_family_name))

#         for model_name, model in model_family.items():
#             print("Time: {}, predicting with model: {}".format(t.now(), model_name))
#             if model_family == 'baseline':
#                 if training:
#                     prediction = algo(train, test_df, model)
#                 else: # predicting
#                     prediction = algo(train_df.copy(), test_df.copy(), model)
#             else:
#                 prediction = algo(train_df, test_df, model)
#             print("Time: {}, Saving results of {}...\n".format(t.now(), model_name))
#             prediction.to_csv("{}{}_predictions({}).csv".format(saving_folder, model_name, t.now()))
#             predictions[model_name] = prediction
        
#     return predictions, test_df


def load_predictions(reading_folder):
    def get_model_name(file_name):
        results = file_name.split('_predictions')
        return results[0]
        
    pred_array = [f for f in listdir(reading_folder) if (isfile(join(reading_folder, f)) and "ground_truth" not in f)]
    print("[load_predictions] files: {}".format(pred_array)) 
    # Set user, col indices
    predictions = pd.read_csv(join(reading_folder, pred_array[0]), index_col=0).copy().reset_index(drop=True)
    predictions = predictions.drop(['Rating'], axis=1)
    predictions = predictions.sort_values(by=['User', 'Movie'])

    for i, pred in enumerate(pred_array):
        print("Reading {}/{} : {}...".format(i + 1, len(pred_array), pred))
        p = pd.read_csv(join(reading_folder, pred), index_col=0).sort_values(by=['User', 'Movie']).reset_index(drop=True)
        p = p.rename(index=str, columns={'Rating': get_model_name(pred)})
        predictions = pd.merge(predictions, p, how='outer', on=['User', 'Movie']).reset_index(drop=True)
    
    return predictions

def optimize(models, ground_truth, folder):
    t = Timer()
    t.start()
    print("Loading predictions from {}....".format(folder))
    predictions = load_predictions(folder)
    print("Time: {}, Finished loading.".format(t.now()))
    t.stop(verbose= False)
    
    # Initialize first weights (- nb columns for User, Movie)
    w0 = [1/(len(predictions.columns) - 2) for i in range(len(predictions.columns) - 2)]
    
    print("Optimizing...")
    t.start()
    res = sco.minimize(evaluate_stacking, w0, method='SLSQP', args=(models, predictions, ground_truth), options={'maxiter': 1000, 'disp': True})
    print("Time: {}. Optimization done.".format(t.now()))
    t.stop()
    
    return res, predictions

def evaluate_stacking(weights, models, predictions, ground_truth):
    # Get stacking results
    user_movie = predictions[['User', 'Movie']]
    truth = pd.merge(user_movie, ground_truth, on=['User', 'Movie'], how='inner').reset_index(drop=True)
    pred = stack(weights, predictions, models)
    return compute_rmse(pred, truth)

def stack(weights, predictions, models):
    stacked = np.zeros(predictions.shape[0])
    idx = 0
    for key, model_fam in models.items():
        for name in model_fam.keys():
            weight = weights[idx]
            stacked = stacked + weight * predictions[name]
            idx = idx + 1
    
    pred= predictions[['User', 'Movie']].copy()
    pred['Rating'] = stacked
    return pred

def get_best_weights(res, models, predictions, ground_truth):
    # Create best dictionnary
    best_dict = {}
    idx = 0
    for key, model_family in models.items():
        best_dict[key] = dict()
        for name in model_family.keys():
            best_dict[key][name] = res.x[idx]
            idx = idx + 1
    
    print("Best weights: \n {}".format(best_dict))
    # test
    rmse = evaluate_stacking(res.x, models, predictions, ground_truth)
    print("Best weights rmse: {}".format(rmse))
    return best_dict, rmse


def predict(weight_dict):
    print("Predicting....")
#     predictions, _ = predict_and_save(folder_predict, training=False)
    predictions = load_predictions(folder_predict)
    print("Finished loading.")
    
    stacked = np.zeros(predictions.shape[0])
    for key, model_fam in models.items():
        weights = weight_dict[key]
        for name in model_fam.keys():
            weight = weights[name]
            print("Stacking {} * {}...".format(weight, name))
            stacked = stacked + weight * predictions[name]
    
    pred = predictions[['User', 'Movie']].copy()
    pred['Rating'] = stacked
    return pred


if __name__ == '__main__':
    folder = "./predict_save/"
    folder_predict = "./train_predictions/"
    models = load_models()
    # Predict & save in advance
#     predictions, ground_truth = predict_and_save(folder)
#     _, _ = predict_and_save(folder_predict, training=False)
    ground_truth = pd.read_csv(folder + "ground_truth.csv")
    res, predictions_tr = optimize(models, ground_truth, folder)
    best_dict, rmse = get_best_weights(res, models, predictions_tr, ground_truth)
    predictions = predict(best_dict)
    submission = create_csv_submission(predictions)
    submission.to_csv("./predictions_tr/blended_baseline.csv")