"""
Main Author: Will LeVine
Corresponding Email: levinewill@icloud.com
"""
from .progressive_learner import ClassificationProgressiveLearner
from .transformers import TreeClassificationTransformer
from .voters import TreeClassificationVoter
from .deciders import SimpleArgmaxAverage
import numpy as np


class LifelongClassificationForest(ClassificationProgressiveLearner):
    """
    A class used to represent a lifelong classification forest.

    Parameters
    ----------
    n_estimators : int, default=100
        The number of estimators used in the Lifelong Classification Forest

    default_tree_construction_proportion : int, default=0.67
        The proportions of the input data set aside to train each decision
        tree. The remainder of the data is used to fill in voting posteriors.
        This is used if 'tree_construction_proportion' is not fed to add_task.

    default_finite_sample_correction : bool, default=False
        Boolean indicating whether this learner will have finite sample correction.
        This is used if 'finite_sample_correction' is not fed to add_task.

    default_max_depth : int, default=30
        The maximum depth of a tree in the Lifelong Classification Forest.
        This is used if 'max_depth' is not fed to add_task.

    Attributes
    ----------
    pl_ : ClassificationProgressiveLearner
        Internal ClassificationProgressiveLearner used to train and make
        inference.
    """

    def __init__(
        self,
        n_estimators=100,
        default_tree_construction_proportion=0.67,
        default_finite_sample_correction=False,
        default_max_depth=30,
    ):
        self.n_estimators = n_estimators
        self.default_tree_construction_proportion = default_tree_construction_proportion
        self.default_finite_sample_correction = default_finite_sample_correction
        self.default_max_depth = default_max_depth
        self.pl_ = ClassificationProgressiveLearner(
            default_transformer_class=TreeClassificationTransformer,
            default_transformer_kwargs={},
            default_voter_class=TreeClassificationVoter,
            default_voter_kwargs={
                "finite_sample_correction": default_finite_sample_correction
            },
            default_decider_class=SimpleArgmaxAverage,
            default_decider_kwargs={},
        )

    def add_task(
        self,
        X,
        y,
        task_id=None,
        tree_construction_proportion="default",
        finite_sample_correction="default",
        max_depth="default",
    ):
        """
        adds a task with id task_id, max tree depth max_depth, given input data matrix X
        and output data matrix y, to the Lifelong Classification Forest. Also splits
        data for training and voting based on tree_construction_proportion and uses the
        value of finite_sample_correction to determine whether the learner will have
        finite sample correction.

        Parameters
        ----------
        X : ndarray
            The input data matrix.

        y : ndarray
            The output (response) data matrix.

        task_id : obj, default=None
            The id corresponding to the task being added.

        tree_construction_proportion : int or str, default='default'
            The proportions of the input data set aside to train each decision
            tree. The remainder of the data is used to fill in voting posteriors.
            The default is used if 'default' is provided.

        finite_sample_correction : bool or str, default='default'
            Boolean indicating whether this learner will have finite sample correction.
            The default is used if 'default' is provided.

        max_depth : int or str, default='default'
            The maximum depth of a tree in the Lifelong Classification Forest.
            The default is used if 'default' is provided.

        Returns
        -------
        self : LifelongClassificationForest
            The object itself.
        """
        if tree_construction_proportion == "default":
            tree_construction_proportion = self.default_tree_construction_proportion
        if finite_sample_correction == "default":
            finite_sample_correction = self.default_finite_sample_correction
        if max_depth == "default":
            max_depth = self.default_max_depth

        self.pl_.add_task(
            X,
            y,
            task_id=task_id,
            transformer_voter_decider_split=[
                tree_construction_proportion,
                1 - tree_construction_proportion,
                0,
            ],
            num_transformers=self.n_estimators,
            transformer_kwargs={"kwargs": {"max_depth": max_depth}},
            voter_kwargs={
                "classes": np.unique(y),
                "finite_sample_correction": finite_sample_correction,
            },
            decider_kwargs={"classes": np.unique(y)},
        )
        return self

    def add_transformer(self, X, y, transformer_id=None, max_depth="default"):
        """
        adds a transformer with id transformer_id and max tree depth max_depth, trained on
        given input data matrix, X, and output data matrix, y, to the Lifelong Classification Forest.
        Also trains the voters and deciders from new transformer to previous tasks, and will
        train voters and deciders from this transformer to all new tasks.

        Parameters
        ----------
        X : ndarray
            The input data matrix.

        y : ndarray
            The output (response) data matrix.

        transformer_id : obj, default=None
            The id corresponding to the transformer being added.

        max_depth : int or str, default='default'
            The maximum depth of a tree in the UncertaintyForest.
            The default is used if 'default' is provided.

        Returns
        -------
        self : LifelongClassificationForest
            The object itself.
        """
        if max_depth == "default":
            max_depth = self.default_max_depth

        self.pl_.add_transformer(
            X,
            y,
            transformer_kwargs={"kwargs": {"max_depth": max_depth}},
            transformer_id=transformer_id,
            num_transformers=self.n_estimators,
        )

        return self

    def predict_proba(self, X, task_id):
        """
        estimates class posteriors under task_id for each example in input data X.

        Parameters
        ----------
        X : ndarray
            The input data matrix.

        task_id:
            The id corresponding to the task being mapped to.

        Returns
        -------
        y_proba_hat : ndarray of shape [n_samples, n_classes]
            posteriors per example
        """
        return self.pl_.predict_proba(X, task_id)

    def predict(self, X, task_id):
        """
        predicts class labels under task_id for each example in input data X.

        Parameters
        ----------
        X : ndarray
            The input data matrix.

        task_id : obj
            The id corresponding to the task being mapped to.

        Returns
        -------
        y_hat : ndarray of shape [n_samples]
            predicted class label per example
        """
        return self.pl_.predict(X, task_id)


class UncertaintyForest:
    """
    A class used to represent an uncertainty forest.

    Parameters
    ----------
    n_estimators : int, default=100
        The number of trees in the UncertaintyForest

    finite_sample_correction : bool, default=False
        Boolean indicating whether this learner
        will use finite sample correction

    max_depth : int, default=30
        The maximum depth of a tree in the UncertaintyForest

    Attributes
    ----------
    lf_ : LifelongClassificationForest
        Internal LifelongClassificationForest used to train and make
        inference.
    """

    def __init__(self, n_estimators=100, finite_sample_correction=False, max_depth=30):
        self.n_estimators = n_estimators
        self.finite_sample_correction = finite_sample_correction
        self.max_depth = max_depth

    def fit(self, X, y):
        """
        fits forest to data X with labels y

        Parameters
        ----------
        X : array of shape [n_samples, n_features]
            The data that will be trained on

        y : array of shape [n_samples]
            The label for cluster membership of the given data

        Returns
        -------
        self : UncertaintyForest
            The object itself.
        """
        self.lf_ = LifelongClassificationForest(
            n_estimators=self.n_estimators,
            default_finite_sample_correction=self.finite_sample_correction,
            default_max_depth=self.max_depth,
        )
        self.lf_.add_task(X, y, task_id=0)
        return self

    def predict_proba(self, X):
        """
        estimates class posteriors for each example in input data X.

        Parameters
        ----------
        X : array of shape [n_samples, n_features]
            The data whose posteriors we are estimating.

        Returns
        -------
        y_proba_hat : ndarray of shape [n_samples, n_classes]
            posteriors per example
        """
        return self.lf_.predict_proba(X, 0)

    def predict(self, X):
        """
        predicts class labels for each example in input data X.

        Parameters
        ----------
        X : array of shape [n_samples, n_features]
            The data on which we are performing inference.

        Returns
        -------
        y_hat : ndarray of shape [n_samples]
            predicted class label per example
        """
        return self.lf_.predict(X, 0)
