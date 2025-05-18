"""
Data analysis module for Parlant.

This module provides functionality for analyzing tabular data, including
descriptive statistics, correlation analysis, and feature importance.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from parlant.core.loggers import Logger


class CorrelationMethod(str, Enum):
    """Methods for calculating correlation."""
    
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"


class FeatureImportanceMethod(str, Enum):
    """Methods for calculating feature importance."""
    
    RANDOM_FOREST = "random_forest"
    MUTUAL_INFO = "mutual_info"
    CHI2 = "chi2"
    ANOVA = "anova"


@dataclass
class DataAnalysisOptions:
    """Options for data analysis."""
    
    # Descriptive statistics
    include_numeric: bool = True
    include_categorical: bool = True
    
    # Correlation analysis
    correlation_method: CorrelationMethod = CorrelationMethod.PEARSON
    correlation_min_value: float = 0.0
    
    # Feature importance
    target_column: Optional[str] = None
    feature_importance_method: FeatureImportanceMethod = FeatureImportanceMethod.RANDOM_FOREST
    n_top_features: int = 10
    
    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)


class DataAnalyzer:
    """Data analyzer for tabular data."""
    
    def __init__(self, logger: Logger):
        """Initialize the data analyzer.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def analyze_data(self, df: pd.DataFrame, options: Optional[DataAnalysisOptions] = None) -> Dict[str, Any]:
        """Analyze a DataFrame and return various statistics and insights.
        
        Args:
            df: DataFrame to analyze
            options: Options for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        if options is None:
            options = DataAnalysisOptions()
            
        self.logger.info(f"Analyzing DataFrame with shape {df.shape}")
        
        results = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": self._analyze_missing_values(df),
        }
        
        # Descriptive statistics
        if options.include_numeric:
            results["numeric_stats"] = self._analyze_numeric_columns(df)
            
        if options.include_categorical:
            results["categorical_stats"] = self._analyze_categorical_columns(df)
            
        # Correlation analysis
        results["correlation"] = self._analyze_correlation(df, options.correlation_method, options.correlation_min_value)
        
        # Feature importance (if target column is specified)
        if options.target_column and options.target_column in df.columns:
            results["feature_importance"] = self._analyze_feature_importance(
                df, 
                options.target_column, 
                options.feature_importance_method,
                options.n_top_features
            )
            
        return results
        
    def _analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing values in a DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary containing missing value analysis
        """
        missing_count = df.isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        
        return {
            "count": missing_count.to_dict(),
            "percent": missing_percent.to_dict(),
            "total_missing": missing_count.sum(),
            "total_missing_percent": (missing_count.sum() / (df.size)) * 100
        }
        
    def _analyze_numeric_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Analyze numeric columns in a DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary containing numeric column analysis
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        
        if len(numeric_cols) == 0:
            return {}
            
        self.logger.info(f"Analyzing {len(numeric_cols)} numeric columns")
        
        result = {}
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            result[col] = {
                "count": len(col_data),
                "mean": col_data.mean(),
                "median": col_data.median(),
                "std": col_data.std(),
                "min": col_data.min(),
                "max": col_data.max(),
                "q1": col_data.quantile(0.25),
                "q3": col_data.quantile(0.75),
                "iqr": col_data.quantile(0.75) - col_data.quantile(0.25),
                "skew": col_data.skew(),
                "kurtosis": col_data.kurtosis(),
            }
            
        return result
        
    def _analyze_categorical_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Analyze categorical columns in a DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary containing categorical column analysis
        """
        categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns
        
        if len(categorical_cols) == 0:
            return {}
            
        self.logger.info(f"Analyzing {len(categorical_cols)} categorical columns")
        
        result = {}
        for col in categorical_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            value_counts = col_data.value_counts()
            
            result[col] = {
                "count": len(col_data),
                "unique_values": col_data.nunique(),
                "top_values": value_counts.head(5).to_dict(),
                "top_percent": (value_counts.head(5) / len(col_data) * 100).to_dict(),
            }
            
        return result
        
    def _analyze_correlation(
        self, 
        df: pd.DataFrame, 
        method: CorrelationMethod = CorrelationMethod.PEARSON,
        min_value: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """Analyze correlation between numeric columns in a DataFrame.
        
        Args:
            df: DataFrame to analyze
            method: Correlation method to use
            min_value: Minimum absolute correlation value to include
            
        Returns:
            Dictionary containing correlation analysis
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        
        if len(numeric_cols) < 2:
            return {}
            
        self.logger.info(f"Analyzing correlation using {method} method")
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr(method=method)
        
        # Convert to dictionary, filtering by min_value
        result = {}
        for col1 in corr_matrix.columns:
            result[col1] = {}
            for col2 in corr_matrix.columns:
                if col1 != col2 and abs(corr_matrix.loc[col1, col2]) >= min_value:
                    result[col1][col2] = corr_matrix.loc[col1, col2]
                    
        return result
        
    def _analyze_feature_importance(
        self, 
        df: pd.DataFrame, 
        target_column: str,
        method: FeatureImportanceMethod = FeatureImportanceMethod.RANDOM_FOREST,
        n_top_features: int = 10
    ) -> Dict[str, float]:
        """Analyze feature importance for predicting a target column.
        
        Args:
            df: DataFrame to analyze
            target_column: Target column to predict
            method: Method for calculating feature importance
            n_top_features: Number of top features to return
            
        Returns:
            Dictionary containing feature importance scores
        """
        try:
            # Get feature columns (exclude target)
            feature_cols = [col for col in df.columns if col != target_column]
            
            # Handle categorical features
            X = pd.get_dummies(df[feature_cols], drop_first=True)
            y = df[target_column]
            
            self.logger.info(f"Analyzing feature importance using {method} method")
            
            if method == FeatureImportanceMethod.RANDOM_FOREST:
                from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
                
                # Determine if classification or regression
                if pd.api.types.is_numeric_dtype(y):
                    model = RandomForestRegressor(n_estimators=100, random_state=42)
                else:
                    model = RandomForestClassifier(n_estimators=100, random_state=42)
                    
                model.fit(X, y)
                importance = model.feature_importances_
                
            elif method == FeatureImportanceMethod.MUTUAL_INFO:
                if pd.api.types.is_numeric_dtype(y):
                    from sklearn.feature_selection import mutual_info_regression
                    importance = mutual_info_regression(X, y)
                else:
                    from sklearn.feature_selection import mutual_info_classif
                    importance = mutual_info_classif(X, y)
                    
            elif method == FeatureImportanceMethod.CHI2:
                from sklearn.feature_selection import chi2, SelectKBest
                
                # Chi2 requires non-negative features
                if (X < 0).any().any():
                    self.logger.warning("Chi2 requires non-negative features. Using absolute values.")
                    X = X.abs()
                    
                if not pd.api.types.is_numeric_dtype(y):
                    from sklearn.preprocessing import LabelEncoder
                    y = LabelEncoder().fit_transform(y)
                    
                selector = SelectKBest(chi2, k='all')
                selector.fit(X, y)
                importance = selector.scores_
                
            elif method == FeatureImportanceMethod.ANOVA:
                from sklearn.feature_selection import f_classif, SelectKBest
                
                if not pd.api.types.is_numeric_dtype(y):
                    from sklearn.preprocessing import LabelEncoder
                    y = LabelEncoder().fit_transform(y)
                    
                selector = SelectKBest(f_classif, k='all')
                selector.fit(X, y)
                importance = selector.scores_
                
            else:
                raise ValueError(f"Unsupported feature importance method: {method}")
                
            # Create feature importance dictionary
            feature_importance = dict(zip(X.columns, importance))
            
            # Sort by importance and take top N
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:n_top_features])
            
            return sorted_importance
            
        except Exception as e:
            self.logger.error(f"Error calculating feature importance: {e}")
            return {}
