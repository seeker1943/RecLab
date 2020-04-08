"""A set of utility functions for testing."""
import collections
import numpy as np

from reclab import data_utils

NUM_USERS_ML100K = 943
NUM_ITEMS_ML100K = 1682


def test_predict_ml100k(recommender, rmse_threshold=1.1, seed=None):
    """Test that recommender predicts well and that it gets better with more data."""
    users, items, ratings = data_utils.read_dataset('ml-100k')
    train_ratings, test_ratings = data_utils.split_ratings(ratings, 0.9, shuffle=True, seed=seed)
    train_ratings_1, train_ratings_2 = data_utils.split_ratings(train_ratings, 0.5)
    recommender.reset(users, items, train_ratings_1)
    user_item = [(key[0], key[1], val[1]) for key, val in test_ratings.items()]
    preds = recommender.predict(user_item)
    targets = [t[0] for t in test_ratings.values()]
    rmse1 = rmse(preds, targets)

    # We should get a relatively low RMSE here.
    assert rmse1 < rmse_threshold

    recommender.update(ratings=train_ratings_2)
    preds = recommender.predict(user_item)
    rmse2 = rmse(preds, targets)

    # The RMSE should have reduced.
    assert rmse1 > rmse2


def test_recommend_simple(recommender):
    """Test that recommender will recommend reasonable items in simple setting."""
    users = {0: np.zeros((0,)),
             1: np.zeros((0,))}
    items = {0: np.zeros((0,)),
             1: np.zeros((0,)),
             2: np.zeros((0,))}
    ratings = {(0, 0): (5, np.zeros((0,))),
               (0, 1): (1, np.zeros((0,))),
               (0, 2): (5, np.zeros((0,))),
               (1, 0): (5, np.zeros((0,)))}
    recommender.reset(users, items, ratings)
    user_contexts = collections.OrderedDict([(1, np.zeros((0,)))])
    recs, _ = recommender.recommend(user_contexts, 1)
    recommender.predict([(1, 1, np.zeros(0,)), (1, 2, np.zeros(0,))])
    assert recs.shape == (1, 1)
    # The recommender should have recommended the item that user0 rated the highest.
    assert recs[0, 0] == 2


def rmse(predictions, targets):
    """Compute the root mean squared error (RMSE) between prediction and target vectors."""
    return np.sqrt(((predictions - targets) ** 2).mean())
