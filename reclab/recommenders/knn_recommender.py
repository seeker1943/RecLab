"""The implementation for a neighborhood based recommender."""
import heapq

import numpy as np
import scipy.sparse
import scipy.sparse.linalg

from . import recommender


class KNNRecommender(recommender.PredictRecommender):
    """A neighborhood based collaborative filtering algorithm.

    The class supports both user and item based collaborative filtering.

    Parameters
    ----------
    shrinkage : float
        The shrinkage parameter applied to the similarity measure.
    neighborhood_size : int
        The number of users/items to consider when estimating a rating.
    user_based : bool
        If this variable is set to true the created object will use user-based collaborative
        filtering, otherwise it will use item-based collaborative filtering.
    use_content : bool
        Whether to use the user/item features when computing the similarity measure.
    use_means : bool
        Whether to adjust the ratings based on the mean rating of each user/item.

    """

    def __init__(self, shrinkage=0, neighborhood_size=40,
                 user_based=True, use_content=True, use_means=True):
        """Create a new neighborhood recommender."""
        super().__init__()
        self._shrinkage = shrinkage
        self._neighborhood_size = neighborhood_size
        self._user_based = user_based
        self._use_content = use_content
        self._use_means = use_means
        self._feature_matrix = scipy.sparse.csr_matrix((0, 0))
        self._means = np.empty(0)
        self._similarity_matrix = np.empty((0, 0))
        self._ratings_matrix = np.empty((0, 0))
        self._hyperparameter.update(locals())

        # We only want the function arguments so remove class related objects.
        del self._hyperparameters['self']
        del self._hyperparameters['__class__']

    @property
    def name(self):  # noqa: D102
        return 'knn'

    def reset(self, users=None, items=None, ratings=None):  # noqa: D102
        self._feature_matrix = scipy.sparse.csr_matrix((0, 0))
        self._similarity_matrix = np.empty((0, 0))
        self._means = np.empty(0)
        self._ratings_matrix = np.empty((0, 0))
        super().reset(users, items, ratings)

    def update(self, users=None, items=None, ratings=None):  # noqa: D102
        super().update(users, items, ratings)
        if self._user_based:
            self._feature_matrix = scipy.sparse.csr_matrix(self._ratings)
        else:
            self._feature_matrix = scipy.sparse.csr_matrix(self._ratings.T)
        self._means = divide_zero(flatten(self._feature_matrix.sum(axis=1)),
                                  self._feature_matrix.getnnz(axis=1))
        if self._use_content:
            if self._user_based:
                self._feature_matrix = scipy.sparse.hstack([self._feature_matrix, self._users])
            else:
                self._feature_matrix = scipy.sparse.hstack([self._feature_matrix, self._items])
        self._similarity_matrix = cosine_similarity(self._feature_matrix, self._feature_matrix,
                                                    self._shrinkage)
        # TODO: this may not be the best way to store ratings, but it does speed access
        self._ratings_matrix = self._ratings.A

    def _predict(self, user_item):  # noqa: D102
        preds = []
        for user_id, item_id, _ in user_item:
            if self._user_based:
                relevant_idxs = nlargest_indices(self._neighborhood_size,
                                                 self._similarity_matrix[user_id])
                similarities = self._similarity_matrix[relevant_idxs, user_id]
                ratings = self._ratings_matrix[relevant_idxs, item_id].ravel()
                mean = self._means[user_id]
            else:
                relevant_idxs = nlargest_indices(self._neighborhood_size,
                                                 self._similarity_matrix[item_id])
                similarities = self._similarity_matrix[relevant_idxs, item_id]
                ratings = self._ratings_matrix.T[relevant_idxs, user_id].ravel()
                mean = self._means[item_id]
            relevant_means = self._means[relevant_idxs]
            nonzero = ratings != 0
            ratings = ratings[nonzero]
            similarities = similarities[nonzero]
            # ensure that we aren't weighting by all 0
            if np.all(np.isclose(similarities, 0)):
                similarities = np.ones_like(similarities)
            if self._use_means:
                if len(ratings) == 0:
                    preds.append(mean)
                else:
                    preds.append(mean + np.average(ratings - relevant_means[nonzero],
                                                   weights=similarities))
            else:
                if len(ratings) == 0:
                    preds.append(0)
                else:
                    preds.append(np.average(ratings, weights=similarities))

        return np.array(preds)


def cosine_similarity(X, Y, shrinkage):
    """Compute the cosine similarity between each row vector in each matrix X and Y.

    Parameters
    ----------
    X : np.matrix
        The first matrix for which to compute the cosine similarity.
    Y : np.matrix
        The second matrix for which to compute the cosine similarity.
    shrinkage : float
        The amount of shrinkage to apply to the similarity computation.

    Returns
    -------
    similarity : np.ndarray
        The similarity array between each pairs of row, where similarity[i, j]
        is the cosine similarity between X[i] and Y[j].

    """
    return divide_zero((X @ Y.T).A, scipy.sparse.linalg.norm(X, axis=1)[:, np.newaxis] *
                       scipy.sparse.linalg.norm(Y, axis=1)[np.newaxis, :] + shrinkage)


def nlargest_indices(n, iterable):
    """Given an iterable, computes the indices of the n largest items.

    Parameters
    ----------
    n : int
        How many indices to retrieve.
    iterable : iterable
        The iterable from which to compute the n largest indices.

    Returns
    -------
    largest : list of int
        The n largest indices where largest[i] is the index of the i-th largest index.

    """
    nlargest = heapq.nlargest(n, enumerate(iterable),
                              key=lambda x: x[1])
    return [i[0] for i in nlargest]


def flatten(matrix):
    """Given a matrix return a flattened numpy array."""
    return matrix.A.ravel()


def divide_zero(num, denom):
    """Divide a and b but return 0 instead of nan for divide by 0."""
    # TODO: is this the desired zero-division behavior?
    return np.divide(num, denom, out=np.zeros_like(num), where=(denom != 0))
