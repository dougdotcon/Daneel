"""
Machine learning module for Daneel.

This module provides functionality for training and evaluating machine learning models
on tabular data, including regression, classification, and clustering.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import pickle
import os
import json

from Daneel.core.loggers import Logger


class ModelType(str, Enum):
    """Types of machine learning models."""

    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVM = "svm"
    KNN = "knn"
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    NEURAL_NETWORK = "neural_network"


class EvaluationMetric(str, Enum):
    """Metrics for evaluating machine learning models."""

    # Regression metrics
    MSE = "mse"  # Mean Squared Error
    RMSE = "rmse"  # Root Mean Squared Error
    MAE = "mae"  # Mean Absolute Error
    R2 = "r2"  # R-squared

    # Classification metrics
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
    AUC = "auc"  # Area Under ROC Curve

    # Clustering metrics
    SILHOUETTE = "silhouette"
    CALINSKI_HARABASZ = "calinski_harabasz"
    DAVIES_BOULDIN = "davies_bouldin"


@dataclass
class ModelTrainingOptions:
    """Options for model training."""

    # General options
    test_size: float = 0.2
    random_state: int = 42

    # Feature engineering
    handle_categorical: bool = True
    handle_missing: bool = True
    normalize: bool = True

    # Model-specific options
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    # Training options
    cross_validation: bool = True
    n_folds: int = 5

    # Evaluation options
    evaluation_metrics: List[EvaluationMetric] = field(default_factory=list)

    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)


class ModelTrainer:
    """Machine learning model trainer."""

    def __init__(self, logger: Logger):
        """Initialize the model trainer.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def train_model(
        self,
        df: pd.DataFrame,
        target_column: str,
        model_type: ModelType,
        feature_columns: Optional[List[str]] = None,
        options: Optional[ModelTrainingOptions] = None
    ) -> Dict[str, Any]:
        """Train a machine learning model.

        Args:
            df: DataFrame containing the data
            target_column: Column to predict
            model_type: Type of model to train
            feature_columns: Columns to use as features (if None, use all except target)
            options: Training options

        Returns:
            Dictionary containing the trained model and evaluation results
        """
        if options is None:
            options = ModelTrainingOptions()

        self.logger.info(f"Training {model_type} model to predict {target_column}")

        # Prepare data
        X, y, feature_names = self._prepare_data(df, target_column, feature_columns, options)

        # Split data into train and test sets
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=options.test_size, random_state=options.random_state
        )

        # Train model
        model, is_classifier = self._train_model_by_type(model_type, X_train, y_train, options)

        # Evaluate model
        evaluation = self._evaluate_model(model, X_test, y_test, is_classifier, options)

        # Feature importance (if available)
        feature_importance = self._get_feature_importance(model, feature_names)

        return {
            "model": model,
            "model_type": model_type,
            "is_classifier": is_classifier,
            "feature_names": feature_names,
            "evaluation": evaluation,
            "feature_importance": feature_importance
        }

    def train_clustering_model(
        self,
        df: pd.DataFrame,
        model_type: ModelType,
        feature_columns: Optional[List[str]] = None,
        options: Optional[ModelTrainingOptions] = None
    ) -> Dict[str, Any]:
        """Train a clustering model.

        Args:
            df: DataFrame containing the data
            model_type: Type of clustering model to train
            feature_columns: Columns to use as features (if None, use all)
            options: Training options

        Returns:
            Dictionary containing the trained model and evaluation results
        """
        if options is None:
            options = ModelTrainingOptions()

        self.logger.info(f"Training {model_type} clustering model")

        # Prepare data (without target)
        if feature_columns is None:
            feature_columns = df.select_dtypes(include=["number"]).columns.tolist()

        X = df[feature_columns].copy()

        # Handle missing values
        if options.handle_missing:
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy="mean")
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

        # Normalize data
        if options.normalize:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

        # Train clustering model
        if model_type == ModelType.KMEANS:
            from sklearn.cluster import KMeans

            # Determine optimal number of clusters if not specified
            n_clusters = options.hyperparameters.get("n_clusters")
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(X)

            model = KMeans(
                n_clusters=n_clusters,
                random_state=options.random_state,
                **{k: v for k, v in options.hyperparameters.items() if k != "n_clusters"}
            )

        elif model_type == ModelType.DBSCAN:
            from sklearn.cluster import DBSCAN
            model = DBSCAN(**options.hyperparameters)

        else:
            raise ValueError(f"Unsupported clustering model type: {model_type}")

        # Fit model
        model.fit(X)

        # Get cluster labels
        labels = model.labels_

        # Evaluate clustering
        evaluation = self._evaluate_clustering(X, labels, model_type)

        return {
            "model": model,
            "model_type": model_type,
            "feature_names": feature_columns,
            "labels": labels,
            "n_clusters": len(set(labels)) - (1 if -1 in labels else 0),  # Exclude noise points
            "evaluation": evaluation
        }

    def save_model(self, model_result: Dict[str, Any], file_path: str) -> None:
        """Save a trained model to a file.

        Args:
            model_result: Model result from train_model or train_clustering_model
            file_path: Path to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Extract model and metadata
        model = model_result["model"]
        metadata = {k: v for k, v in model_result.items() if k != "model"}

        # Convert numpy arrays to lists for JSON serialization
        if "labels" in metadata and isinstance(metadata["labels"], np.ndarray):
            metadata["labels"] = metadata["labels"].tolist()

        # Save model with pickle
        with open(file_path, "wb") as f:
            pickle.dump(model, f)

        # Save metadata as JSON
        metadata_path = f"{os.path.splitext(file_path)[0]}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, default=lambda o: str(o) if isinstance(o, (np.ndarray, pd.Series)) else o)

        self.logger.info(f"Model saved to {file_path}")
        self.logger.info(f"Metadata saved to {metadata_path}")

    def load_model(self, file_path: str) -> Dict[str, Any]:
        """Load a trained model from a file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing the model and metadata
        """
        # Load model with pickle
        with open(file_path, "rb") as f:
            model = pickle.load(f)

        # Load metadata if available
        metadata_path = f"{os.path.splitext(file_path)[0]}_metadata.json"
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

        # Combine model and metadata
        result = {"model": model, **metadata}

        self.logger.info(f"Model loaded from {file_path}")

        return result

    def _prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: Optional[List[str]],
        options: ModelTrainingOptions
    ) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare data for model training.

        Args:
            df: DataFrame containing the data
            target_column: Column to predict
            feature_columns: Columns to use as features
            options: Training options

        Returns:
            Tuple of (X, y, feature_names)
        """
        # Select feature columns
        if feature_columns is None:
            feature_columns = [col for col in df.columns if col != target_column]

        X = df[feature_columns].copy()
        y = df[target_column].copy()

        # Handle categorical features
        if options.handle_categorical:
            X = pd.get_dummies(X, drop_first=True)

        # Handle missing values
        if options.handle_missing:
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy="mean")
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

        # Normalize data
        if options.normalize:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

        return X, y, X.columns.tolist()

    def _train_model_by_type(
        self,
        model_type: ModelType,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        options: ModelTrainingOptions
    ) -> Tuple[Any, bool]:
        """Train a model based on its type.

        Args:
            model_type: Type of model to train
            X_train: Training features
            y_train: Training target
            options: Training options

        Returns:
            Tuple of (model, is_classifier)
        """
        is_classifier = False

        if model_type == ModelType.LINEAR_REGRESSION:
            from sklearn.linear_model import LinearRegression
            model = LinearRegression(**options.hyperparameters)

        elif model_type == ModelType.LOGISTIC_REGRESSION:
            from sklearn.linear_model import LogisticRegression
            model = LogisticRegression(random_state=options.random_state, **options.hyperparameters)
            is_classifier = True

        elif model_type == ModelType.RANDOM_FOREST:
            # Determine if classification or regression
            if len(np.unique(y_train)) < 10 or not np.issubdtype(y_train.dtype, np.number):
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(random_state=options.random_state, **options.hyperparameters)
                is_classifier = True
            else:
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(random_state=options.random_state, **options.hyperparameters)

        elif model_type == ModelType.GRADIENT_BOOSTING:
            # Determine if classification or regression
            if len(np.unique(y_train)) < 10 or not np.issubdtype(y_train.dtype, np.number):
                from sklearn.ensemble import GradientBoostingClassifier
                model = GradientBoostingClassifier(random_state=options.random_state, **options.hyperparameters)
                is_classifier = True
            else:
                from sklearn.ensemble import GradientBoostingRegressor
                model = GradientBoostingRegressor(random_state=options.random_state, **options.hyperparameters)

        elif model_type == ModelType.SVM:
            from sklearn.svm import SVC, SVR
            # Determine if classification or regression
            if len(np.unique(y_train)) < 10 or not np.issubdtype(y_train.dtype, np.number):
                model = SVC(random_state=options.random_state, probability=True, **options.hyperparameters)
                is_classifier = True
            else:
                model = SVR(**options.hyperparameters)

        elif model_type == ModelType.KNN:
            from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
            # Determine if classification or regression
            if len(np.unique(y_train)) < 10 or not np.issubdtype(y_train.dtype, np.number):
                model = KNeighborsClassifier(**options.hyperparameters)
                is_classifier = True
            else:
                model = KNeighborsRegressor(**options.hyperparameters)

        elif model_type == ModelType.NEURAL_NETWORK:
            from sklearn.neural_network import MLPClassifier, MLPRegressor
            # Determine if classification or regression
            if len(np.unique(y_train)) < 10 or not np.issubdtype(y_train.dtype, np.number):
                model = MLPClassifier(random_state=options.random_state, **options.hyperparameters)
                is_classifier = True
            else:
                model = MLPRegressor(random_state=options.random_state, **options.hyperparameters)

        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Train the model
        model.fit(X_train, y_train)

        return model, is_classifier

    def _evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        is_classifier: bool,
        options: ModelTrainingOptions
    ) -> Dict[str, float]:
        """Evaluate a trained model.

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test target
            is_classifier: Whether the model is a classifier
            options: Training options

        Returns:
            Dictionary of evaluation metrics
        """
        results = {}

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate metrics based on model type
        if is_classifier:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

            # Basic classification metrics
            results["accuracy"] = accuracy_score(y_test, y_pred)

            # For binary classification
            if len(np.unique(y_test)) == 2:
                results["precision"] = precision_score(y_test, y_pred, average="binary")
                results["recall"] = recall_score(y_test, y_pred, average="binary")
                results["f1"] = f1_score(y_test, y_pred, average="binary")

                # AUC requires probability predictions
                if hasattr(model, "predict_proba"):
                    y_prob = model.predict_proba(X_test)[:, 1]
                    results["auc"] = roc_auc_score(y_test, y_prob)
            else:
                # For multiclass classification
                results["precision"] = precision_score(y_test, y_pred, average="weighted")
                results["recall"] = recall_score(y_test, y_pred, average="weighted")
                results["f1"] = f1_score(y_test, y_pred, average="weighted")

                # AUC for multiclass
                if hasattr(model, "predict_proba"):
                    y_prob = model.predict_proba(X_test)
                    results["auc"] = roc_auc_score(y_test, y_prob, multi_class="ovr", average="weighted")
        else:
            # Regression metrics
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

            results["mse"] = mean_squared_error(y_test, y_pred)
            results["rmse"] = np.sqrt(results["mse"])
            results["mae"] = mean_absolute_error(y_test, y_pred)
            results["r2"] = r2_score(y_test, y_pred)

        # Cross-validation if enabled
        if options.cross_validation:
            from sklearn.model_selection import cross_val_score

            # Determine scoring metric
            if is_classifier:
                scoring = "accuracy"
            else:
                scoring = "neg_mean_squared_error"

            cv_scores = cross_val_score(model, X_test, y_test, cv=options.n_folds, scoring=scoring)

            if is_classifier:
                results["cv_accuracy"] = cv_scores.mean()
                results["cv_accuracy_std"] = cv_scores.std()
            else:
                results["cv_neg_mse"] = cv_scores.mean()
                results["cv_neg_mse_std"] = cv_scores.std()

        return results

    def _evaluate_clustering(
        self,
        X: pd.DataFrame,
        labels: np.ndarray,
        model_type: ModelType
    ) -> Dict[str, float]:
        """Evaluate a clustering model.

        Args:
            X: Feature data
            labels: Cluster labels
            model_type: Type of clustering model

        Returns:
            Dictionary of evaluation metrics
        """
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

        results = {}

        # Skip evaluation if all points are in the same cluster
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        if n_clusters <= 1:
            self.logger.warning("Cannot evaluate clustering with only one cluster")
            return {"n_clusters": n_clusters}

        # Filter out noise points for evaluation
        if -1 in labels:
            mask = labels != -1
            X_filtered = X[mask]
            labels_filtered = labels[mask]
        else:
            X_filtered = X
            labels_filtered = labels

        # Skip evaluation if there are no valid points after filtering
        if len(X_filtered) <= 1:
            self.logger.warning("Not enough valid points for clustering evaluation")
            return {"n_clusters": n_clusters}

        try:
            # Silhouette score (higher is better)
            results["silhouette"] = silhouette_score(X_filtered, labels_filtered)

            # Calinski-Harabasz Index (higher is better)
            results["calinski_harabasz"] = calinski_harabasz_score(X_filtered, labels_filtered)

            # Davies-Bouldin Index (lower is better)
            results["davies_bouldin"] = davies_bouldin_score(X_filtered, labels_filtered)
        except Exception as e:
            self.logger.error(f"Error calculating clustering metrics: {e}")

        return results

    def _get_feature_importance(self, model: Any, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from a trained model.

        Args:
            model: Trained model
            feature_names: Names of features

        Returns:
            Dictionary mapping feature names to importance scores
        """
        # Check if model has feature_importances_ attribute
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            return dict(zip(feature_names, importances))

        # Check if model has coef_ attribute (linear models)
        elif hasattr(model, "coef_"):
            if len(model.coef_.shape) == 1:
                # Binary classification or regression
                importances = np.abs(model.coef_)
                return dict(zip(feature_names, importances))
            else:
                # Multiclass classification
                importances = np.mean(np.abs(model.coef_), axis=0)
                return dict(zip(feature_names, importances))

        return {}

    def _find_optimal_clusters(self, X: pd.DataFrame, max_clusters: int = 10) -> int:
        """Find the optimal number of clusters using the elbow method.

        Args:
            X: Feature data
            max_clusters: Maximum number of clusters to consider

        Returns:
            Optimal number of clusters
        """
        from sklearn.cluster import KMeans

        self.logger.info("Finding optimal number of clusters")

        # Limit max_clusters to the number of samples
        max_clusters = min(max_clusters, len(X) - 1)

        # Calculate inertia for different numbers of clusters
        inertia = []
        for k in range(1, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(X)
            inertia.append(kmeans.inertia_)

        # Find the elbow point
        from kneed import KneeLocator
        try:
            kneedle = KneeLocator(range(1, max_clusters + 1), inertia, curve="convex", direction="decreasing")
            optimal_k = kneedle.elbow
        except:
            # Fallback if kneed is not available or fails
            optimal_k = 3

        if optimal_k is None:
            optimal_k = 3

        self.logger.info(f"Optimal number of clusters: {optimal_k}")

        return optimal_k

    def predict(
        self,
        model_result: Dict[str, Any],
        data: pd.DataFrame
    ) -> np.ndarray:
        """Make predictions using a trained model.

        Args:
            model_result: Model result from train_model
            data: Data to make predictions on

        Returns:
            Array of predictions
        """
        model = model_result["model"]
        feature_names = model_result["feature_names"]

        # Prepare data
        X = data[feature_names].copy()

        # Make predictions
        return model.predict(X)

    def predict_proba(
        self,
        model_result: Dict[str, Any],
        data: pd.DataFrame
    ) -> np.ndarray:
        """Make probability predictions using a trained classifier.

        Args:
            model_result: Model result from train_model
            data: Data to make predictions on

        Returns:
            Array of probability predictions
        """
        model = model_result["model"]
        feature_names = model_result["feature_names"]
        is_classifier = model_result["is_classifier"]

        if not is_classifier:
            raise ValueError("Probability predictions are only available for classifiers")

        if not hasattr(model, "predict_proba"):
            raise ValueError("Model does not support probability predictions")

        # Prepare data
        X = data[feature_names].copy()

        # Make probability predictions
        return model.predict_proba(X)
