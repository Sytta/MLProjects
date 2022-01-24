# Machine Learning Project 2 - Movie Recommender System 

**Submission ID**: 25003

## Set Up

Warning: This setup has only been tested on Ubuntu 18.04. It is probable that the code won't run on a Windows System. Please make sure that your system has enough space (5G to be sure).

#### Packages where the machine learning algorithms are taken:

Sklearn: https://scikit-learn.org/stable/

Spotlight: https://github.com/maciejkula/spotlight/tree/master/spotlight

Surprise: https://github.com/NicolasHug/Surprise

PyFM: https://github.com/coreylynch/pyFM

1. Make sure that the system has gcc and g++ compilers. If not, please do: ``` sudo apt-get install build-essential ``` in the terminal.
2. Download the all the zip files, unzip and make sure that you have the folder structure described below.
    test_predictions: ~~https://drive.google.com/file/d/1_K_4mr8xuKlzHDWcdz7vw5_zM5aa0kpG/view?usp=sharing~~ (no longer available)
    train_predictions: ~~https://drive.google.com/file/d/13NvkbL_eILzpQtDZvqnI-UTllDgAY3eV/view?usp=sharing~~ (no longer available)
3. Make sure that you have Anaconda installed. If not, you can get the installer here: https://repo.anaconda.com/archive/
4. Go in the folder, run ```conda env create -f MLenv.yml``` in terminal
5. Activate the environment by running ```source activate ML``` in terminal
6. Install Cython by running ``` conda install Cython``` in terminal (for some reason it won't install with the other packages)
7. Install PyFM by running ``` pip install git+https://github.com/coreylynch/pyFM``` in terminal

## Folder Structure

We are assuming the following folder structure:

```
.
├── datas
│   ├── data_train.csv              # Training dataset
│   └── sampleSubmission.csv        # Prediction dataset 
├── src                             
│   ├── als.py                      # ALS algorithm presented in class
│   ├── baseline_helpers.py         # Standardize and recovering from standardize functions
│   ├── baseline.py                 # Baseline algorithms
│   ├── constants.py                # Variables defining the folders
│   ├── helpers.py                  # Helper functions (read, save as csv functions)
│   ├── MFRR.py                     # Sklearn algorithms 
│   ├── produce_predict_csv.py      # Functions to produce the ground_truth / training prediction csvs, and test prediction csvs
│   ├── run.ipynb                   # Jupyter notebook outputing results of code in run.py
│   ├── run.py                      # Produces submission.csv
│   ├── spotlight_helpers.py        # Spotlight algorithms
│   ├── stack.py                    # Functions to stack algorithms together
│   └── surprise_helpers.py         # Surprise algorithms
├── submission.csv                  # Predictions of the ratings of the prediction dataset
├── test_predictions                # Folder containing all the predictions.csv (prediction dataset) produced by different algorithms (Download test_predictions.zip)
│   ├── als_predictions.csv        
│   ├── global_mean_predictions.csv
│   ├── global_median_predictions.csv
│   ├── mfrr_predictions.csv
│   ├── movie_mean_predictions.csv
│   ├── movie_mean_user_habit_predictions.csv
│   ├── movie_mean_user_habit_std_predictions.csv
│   ├── movie_mean_user_habit_std.csv
│   ├── movie_median_predictions.csv
│   ├── movie_median_user_habit_predictions.csv
│   ├── movie_median_user_habit_std_predictions.csv
│   ├── movie_median_user_std_predictions.csv
│   ├── pyfm_predictions.csv
│   ├── spotlight_predictions.csv
│   ├── surprise_knn_predictions.csv
│   ├── surprise_svd_pp_predictions.csv
│   ├── surprise_svd_predictions.csv
│   ├── user_mean_predictions.csv
│   └── user_median_predictions.csv
│  
├── train_predictions               # Folder containing all the predictions.csv (1/2 of the training dataset) produced by different algorithms + ground_truth.csv  (Download test_predictions.zip)
│   ├── als_predictions.csv        
│   ├── global_mean_predictions.csv
│   ├── global_median_predictions.csv
│   ├── ground_truth.csv
│   ├── mfrr_predictions.csv
│   ├── movie_mean_predictions.csv
│   ├── movie_mean_user_habit_predictions.csv
│   ├── movie_mean_user_habit_std_predictions.csv
│   ├── movie_mean_user_habit_std.csv
│   ├── movie_median_predictions.csv
│   ├── movie_median_user_habit_predictions.csv
│   ├── movie_median_user_habit_std_predictions.csv
│   ├── movie_median_user_std_predictions.csv
│   ├── pyfm_predictions.csv
│   ├── spotlight_predictions.csv
│   ├── surprise_knn_predictions.csv
│   ├── surprise_svd_pp_predictions.csv
│   ├── surprise_svd_predictions.csv
│   ├── user_mean_predictions.csv
│   └── user_median_predictions.csv
│  
├── parameters_tuning (the tuning of ALS is found in als.py above)
│   ├── helpers.py                          # Same helpers
│   ├── pyFM_params.py                      # Script to find the best parameters of pyFM
│   ├── spotlight_params.py                 # Script to find the best parameters of spotlight
│   ├── surprise_knn_params.py              # Script to find the best parameters of knn
│   └── surprise_svd_params.py              # Script to find the best parameters of svd 
│
├── MLenv.yml                       # Environment file for Anaconda
└── README.md                       # This file
```

## How to get the submission.csv on CrowdAI?
1. Make sure that you have all the csvs in test_predictions and train_predictions listed above. If you want to generate yourself the csvs, go in src folder and run ```python3 produce_predict_csv.py option(choose a model) ```. 
    The available options are: 

    * ```als ``` (took us about 4.25 hrs) 
    * ```baseline ``` (took us about 20 min)
    * ```mfrr ``` (took us about 50 min)
    * ```pyfm ``` (took us about 2 hrs)
    * ```spotlight ``` (took us about 6 hrs)
    * ```surprise``` (took us about 16 hrs)

    Exemple of run: ```python3 produce_predict_csv.py baseline > produce_baseline.out & ```

2. Once you have all the csv produced and placed under the right folder (you can change ```constants.py``` to choose the folder where you want to put them), go to `src/` and run ```python3 run.py``` or run our jupyter notebook ```run.ipynb```. The submission file will be produce in this root folder.

## Results

We have obtained RMSE of 1.017 on CrowdAI. 

**Submission ID**: 25003

## Possible Issues

* It is possible that with ALS (als.py), the numbers of the predictions might fluctuate a little (from 0.01 to 0.5 differences) in als_predictions.csv (not in submission.csv). We have not found the reason to this and we did not have enought time to investigate further. The small fluctuation does not seem to impact our results.
