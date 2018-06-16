# -*- coding: utf-8 -*-
"""Clustering Based Local Outlier Factor (CBLOF)
"""
# Author: Yue Zhao <yuezhao@cs.toronto.edu>
# License: BSD 2 clause

from __future__ import division
from __future__ import print_function

from sklearn.cluster import MiniBatchKMeans
from sklearn.utils.validation import check_is_fitted
from sklearn.utils.validation import check_array
from sklearn.utils.estimator_checks import check_estimator

from .base import BaseDetector
from ..utils.utility import check_parameter

__all__ = ['CBLOF']


class CBLOF(BaseDetector):
    """The CBLOF operator calculates the outlier score based on cluster-based
    local outlier factor.

    CBLOF takes as an input the data set and the cluster model that was
    generated by a clustering algorithm. It classifies the clusters into small
    clusters and large clusters using the parameters alpha and beta.
    The anomaly score is then calculated based on the size of the cluster the
    point belongs to as well as the distance to the nearest large cluster.

    Use weighting for outlier factor based on the sizes of the clusters as
    proposed in the original publication. Since this might lead to unexpected
    behavior (outliers close to small clusters are not found), it can be
    disabled and outliers scores are solely computed based on their distance to
    the cluster center.

    See :cite:`he2003discovering` for details.

    :param contamination: The amount of contamination of the data set,
        i.e. the proportion of outliers in the data set. Used when fitting to
        define the threshold on the decision function.
    :type contamination: float in (0., 0.5), optional (default=0.1)

    :param n_jobs: The number of jobs to run in parallel for both `fit` and
        `predict`. If -1, then the number of jobs is set to the number of cores
    :type n_jobs: int, optional (default=1)

    :param random_state: If int, random_state is the seed used by the random
        number generator; If RandomState instance, random_state is the random
        number generator; If None, the random number generator is the
        RandomState instance used by `np.random`.
    :type random_state: int, RandomState instance or None, optional
        (default=None)

    :var decision_scores\_: The outlier scores of the training data.
        The higher, the more abnormal. Outliers tend to have higher
        scores. This value is available once the detector is
        fitted.
    :vartype decision_scores\_: numpy array of shape (n_samples,)

    :var threshold\_: The threshold is based on ``contamination``. It is the
        ``n_samples * contamination`` most abnormal samples in
        ``decision_scores_``. The threshold is calculated for generating
        binary outlier labels.
    :vartype threshold\_: float

    :var labels\_: The binary labels of the training data. 0 stands for inliers
        and 1 for outliers/anomalies. It is generated by applying
        ``threshold_`` on ``decision_scores_``.
    :vartype labels\_: int, either 0 or 1
    """

    def __init__(self, algorithm=None, alpha=0.9, beta=5, contamination=0.1,
                 n_jobs=1, random_state=None):
        super(CBLOF, self).__init__(contamination=contamination)
        self.algorithm = algorithm
        self.alpha = alpha
        self.beta = beta
        self.n_jobs = n_jobs
        self.random_state = random_state

    # noinspection PyIncorrectDocstring
    def fit(self, X, y=None):
        """Fit the model using X as training data.

        :param X: Training data. If array or matrix,
            shape [n_samples, n_features],
            or [n_samples, n_samples] if metric='precomputed'.
        :type X: {array-like, sparse matrix, BallTree, KDTree}

        :return: self
        :rtype: object
        """
        # Validate inputs X and y (optional)
        X = check_array(X)
        self._set_n_classes(y)

        # check parameters
        # number of clusters are default to 8
        self._validate_estimator(default=MiniBatchKMeans(n_jobs=self.n_jobs))

        self.base_estimator_.fit(X=X, y=y)

        # Use mahalanabis distance as the outlier score
        self.decision_scores_ = self.detector_.dist_
        self._process_decision_scores()
        return self

    def decision_function(self, X):
        check_is_fitted(self, ['decision_scores_', 'threshold_', 'labels_'])
        X = check_array(X)

        # Computer mahalanobis distance of the samples
        return self.detector_.mahalanobis(X)

    def _validate_estimator(self, default=None):
        """Check the value of alpha and beta and clustering algorithm.
        """

        check_parameter(self.alpha, 0, 1, param_name='alpha',
                        include_left=False, include_right=False)

        check_parameter(self.beta, 0, param_name='alpha',
                        include_left=False, include_right=False)

        if self.base_estimator is not None:
            self.base_estimator_ = self.base_estimator
        else:
            self.base_estimator_ = default

        if self.base_estimator_ is None:
            raise ValueError("clustering algorithm cannot be None")

        check_estimator(self.base_estimator_)
