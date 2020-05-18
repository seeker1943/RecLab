import math
import sys

import numpy as np

sys.path.append('../')
sys.path.append('../../')
from run_utils import get_env_dataset, run_env_experiment
from run_utils import ModelTuner
from reclab.environments import Topics
from env_defaults import TOPICS_STATIC, get_len_trial
from reclab.recommenders import EASE

# ====Step 4====
# S3 storage parameters
bucket_name = 'recsys-eval'
data_dir = 'master'
overwrite = True

# Experiment setup.
n_trials = 10
trial_seeds = [i for i in range(n_trials)]
len_trial = get_len_trial(TOPICS_STATIC)

# Environment setup
environment_name = TOPICS_STATIC['name']
env = Topics(**TOPICS_STATIC['params'], **TOPICS_STATIC['optional_params'])

# Recommender setup
recommender_name = 'EASE'
recommender_class = EASE

# # ====Step 5====
# starting_data = get_env_dataset(env)

# # ====Step 6====
# # Recommender tuning setup
# n_fold = 5
# default_params = {}
# tuner = ModelTuner(starting_data,
#                    default_params,
#                    recommender_class,
#                    n_fold=n_fold,
#                    verbose=True,
#                    bucket_name=bucket_name,
#                    data_dir=data_dir,
#                    environment_name=environment_name,
#                    recommender_name=recommender_name,
#                    overwrite=overwrite)

# # Tune the hyperparameter.
# # Start with a coarse grid.
# lams = np.linspace(10, 1000, 10).tolist()
# tuner.evaluate_grid(lam=lams)

# # It seems that larger regularizers are better, let's increase the grid.
# lams = np.linspace(1000, 10000, 3).tolist()
# tuner.evaluate_grid(lam=lams)

# # It seems that larger regularizers are better, let's increase the grid.
# lams = np.linspace(20000, 100000, 3).tolist()
# tuner.evaluate_grid(lam=lams)

# # Zeroing in on the best range.
# lams = np.linspace(2000, 9000, 10).tolist()
# tuner.evaluate_grid(lam=lams)

# Set regularization to 5000.
lam = 5000

# ====Step 7====
recommender = recommender_class(lam=lam)
for i, seed in enumerate(trial_seeds):
    run_env_experiment(
            [env],
            [recommender],
            [seed],
            len_trial,
            environment_names=[environment_name],
            recommender_names=[recommender_name],
            bucket_name=bucket_name,
            data_dir=data_dir,
            overwrite=overwrite)
