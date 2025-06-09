# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data cleaning and preprocessing utilities."""

import re
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from Daneel.core.loggers import Logger


class ImputationStrategy(str, Enum):
    """Strategies for imputing missing values."""
    
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    FORWARD_FILL = "ffill"
    BACKWARD_FILL = "bfill"
    INTERPOLATE = "interpolate"
    DROP = "drop"


class OutlierDetectionMethod(str, Enum):
    """Methods for detecting outliers."""
    
    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    DBSCAN = "dbscan"


@dataclass
class DataCleaningOptions:
    """Options for data cleaning."""
    
    # Missing value handling
    handle_missing: bool = True
    imputation_strategy: ImputationStrategy = ImputationStrategy.MEAN
    imputation_value: Optional[Any] = None
    
    # Outlier handling
    handle_outliers: bool = False
    outlier_method: OutlierDetectionMethod = OutlierDetectionMethod.Z_SCORE
    outlier_threshold: float = 3.0
    outlier_action: str = "replace"  # "replace", "remove", or "flag"
    
    # Data type conversion
    convert_dtypes: bool = True
    
    # Text cleaning
    clean_text: bool = False
    remove_html: bool = True
    remove_urls: bool = True
    remove_special_chars: bool = False
    lowercase: bool = True
    
    # Duplicate handling
    remove_duplicates: bool = True
    subset_for_duplicates: Optional[List[str]] = None
    
    # Column operations
    columns_to_drop: List[str] = field(default_factory=list)
    columns_to_rename: Dict[str, str] = field(default_factory=dict)
    
    # Custom transformations
    custom_transformations: Dict[str, Callable[[pd.Series], pd.Series]] = field(default_factory=dict)


class DataCleaner:
    """Data cleaner for preprocessing data."""
    
    def __init__(self, logger: Logger):
        """Initialize the data cleaner.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def clean_data(self, df: pd.DataFrame, options: Optional[DataCleaningOptions] = None) -> pd.DataFrame:
        """Clean and preprocess a DataFrame.
        
        Args:
            df: DataFrame to clean
            options: Options for cleaning
            
        Returns:
            Cleaned DataFrame
        """
        if options is None:
            options = DataCleaningOptions()
            
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        self.logger.info(f"Cleaning DataFrame with shape {result.shape}")
        
        # Drop specified columns
        if options.columns_to_drop:
            result = self._drop_columns(result, options.columns_to_drop)
            
        # Rename columns
        if options.columns_to_rename:
            result = self._rename_columns(result, options.columns_to_rename)
            
        # Handle missing values
        if options.handle_missing:
            result = self._handle_missing_values(result, options)
            
        # Handle outliers
        if options.handle_outliers:
            result = self._handle_outliers(result, options)
            
        # Convert data types
        if options.convert_dtypes:
            result = self._convert_dtypes(result)
            
        # Clean text columns
        if options.clean_text:
            result = self._clean_text_columns(result, options)
            
        # Remove duplicates
        if options.remove_duplicates:
            result = self._remove_duplicates(result, options.subset_for_duplicates)
            
        # Apply custom transformations
        if options.custom_transformations:
            result = self._apply_custom_transformations(result, options.custom_transformations)
            
        self.logger.info(f"Cleaned DataFrame has shape {result.shape}")
        
        return result
        
    def _drop_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Drop columns from a DataFrame.
        
        Args:
            df: DataFrame to modify
            columns: Columns to drop
            
        Returns:
            Modified DataFrame
        """
        # Filter to only include columns that exist
        columns_to_drop = [col for col in columns if col in df.columns]
        
        if columns_to_drop:
            self.logger.info(f"Dropping columns: {columns_to_drop}")
            return df.drop(columns=columns_to_drop)
        
        return df
        
    def _rename_columns(self, df: pd.DataFrame, rename_dict: Dict[str, str]) -> pd.DataFrame:
        """Rename columns in a DataFrame.
        
        Args:
            df: DataFrame to modify
            rename_dict: Dictionary mapping old column names to new ones
            
        Returns:
            Modified DataFrame
        """
        # Filter to only include columns that exist
        valid_renames = {old: new for old, new in rename_dict.items() if old in df.columns}
        
        if valid_renames:
            self.logger.info(f"Renaming columns: {valid_renames}")
            return df.rename(columns=valid_renames)
        
        return df
        
    def _handle_missing_values(self, df: pd.DataFrame, options: DataCleaningOptions) -> pd.DataFrame:
        """Handle missing values in a DataFrame.
        
        Args:
            df: DataFrame to modify
            options: Options for handling missing values
            
        Returns:
            Modified DataFrame
        """
        result = df.copy()
        
        # Check if there are any missing values
        missing_count = result.isna().sum().sum()
        if missing_count == 0:
            self.logger.info("No missing values found")
            return result
            
        self.logger.info(f"Handling {missing_count} missing values using strategy: {options.imputation_strategy}")
        
        # Handle missing values based on the strategy
        if options.imputation_strategy == ImputationStrategy.DROP:
            # Drop rows with missing values
            result = result.dropna()
        else:
            # Handle numeric and non-numeric columns separately
            numeric_cols = result.select_dtypes(include=np.number).columns
            non_numeric_cols = result.select_dtypes(exclude=np.number).columns
            
            # Impute numeric columns
            for col in numeric_cols:
                if result[col].isna().any():
                    if options.imputation_strategy == ImputationStrategy.MEAN:
                        result[col] = result[col].fillna(result[col].mean())
                    elif options.imputation_strategy == ImputationStrategy.MEDIAN:
                        result[col] = result[col].fillna(result[col].median())
                    elif options.imputation_strategy == ImputationStrategy.MODE:
                        result[col] = result[col].fillna(result[col].mode()[0])
                    elif options.imputation_strategy == ImputationStrategy.CONSTANT:
                        result[col] = result[col].fillna(options.imputation_value)
                    elif options.imputation_strategy == ImputationStrategy.FORWARD_FILL:
                        result[col] = result[col].ffill()
                    elif options.imputation_strategy == ImputationStrategy.BACKWARD_FILL:
                        result[col] = result[col].bfill()
                    elif options.imputation_strategy == ImputationStrategy.INTERPOLATE:
                        result[col] = result[col].interpolate()
                        
            # Impute non-numeric columns
            for col in non_numeric_cols:
                if result[col].isna().any():
                    if options.imputation_strategy == ImputationStrategy.MODE:
                        result[col] = result[col].fillna(result[col].mode()[0] if not result[col].mode().empty else "")
                    elif options.imputation_strategy == ImputationStrategy.CONSTANT:
                        result[col] = result[col].fillna(options.imputation_value)
                    elif options.imputation_strategy == ImputationStrategy.FORWARD_FILL:
                        result[col] = result[col].ffill()
                    elif options.imputation_strategy == ImputationStrategy.BACKWARD_FILL:
                        result[col] = result[col].bfill()
                    else:
                        # Default to empty string for other strategies
                        result[col] = result[col].fillna("")
                        
        return result
        
    def _handle_outliers(self, df: pd.DataFrame, options: DataCleaningOptions) -> pd.DataFrame:
        """Handle outliers in a DataFrame.
        
        Args:
            df: DataFrame to modify
            options: Options for handling outliers
            
        Returns:
            Modified DataFrame
        """
        result = df.copy()
        
        # Only process numeric columns
        numeric_cols = result.select_dtypes(include=np.number).columns
        
        if len(numeric_cols) == 0:
            self.logger.info("No numeric columns found for outlier detection")
            return result
            
        self.logger.info(f"Detecting outliers using method: {options.outlier_method}")
        
        # Detect and handle outliers based on the method
        if options.outlier_method == OutlierDetectionMethod.Z_SCORE:
            for col in numeric_cols:
                # Calculate z-scores
                z_scores = np.abs((result[col] - result[col].mean()) / result[col].std())
                outliers = z_scores > options.outlier_threshold
                
                if outliers.any():
                    self._handle_detected_outliers(result, col, outliers, options)
                    
        elif options.outlier_method == OutlierDetectionMethod.IQR:
            for col in numeric_cols:
                # Calculate IQR
                q1 = result[col].quantile(0.25)
                q3 = result[col].quantile(0.75)
                iqr = q3 - q1
                
                # Define bounds
                lower_bound = q1 - options.outlier_threshold * iqr
                upper_bound = q3 + options.outlier_threshold * iqr
                
                # Detect outliers
                outliers = (result[col] < lower_bound) | (result[col] > upper_bound)
                
                if outliers.any():
                    self._handle_detected_outliers(result, col, outliers, options)
                    
        elif options.outlier_method in [
            OutlierDetectionMethod.ISOLATION_FOREST,
            OutlierDetectionMethod.LOCAL_OUTLIER_FACTOR,
            OutlierDetectionMethod.DBSCAN
        ]:
            try:
                from sklearn.ensemble import IsolationForest
                from sklearn.neighbors import LocalOutlierFactor
                from sklearn.cluster import DBSCAN
                
                # Prepare data for outlier detection
                X = result[numeric_cols].fillna(0)
                
                if options.outlier_method == OutlierDetectionMethod.ISOLATION_FOREST:
                    model = IsolationForest(contamination=0.1, random_state=42)
                    outliers = model.fit_predict(X) == -1
                elif options.outlier_method == OutlierDetectionMethod.LOCAL_OUTLIER_FACTOR:
                    model = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
                    outliers = model.fit_predict(X) == -1
                elif options.outlier_method == OutlierDetectionMethod.DBSCAN:
                    model = DBSCAN(eps=0.5, min_samples=5)
                    outliers = model.fit_predict(X) == -1
                    
                # Handle outliers for all numeric columns
                for col in numeric_cols:
                    if outliers.any():
                        self._handle_detected_outliers(result, col, outliers, options)
                        
            except ImportError:
                self.logger.warning("scikit-learn is required for advanced outlier detection methods")
                
        return result
        
    def _handle_detected_outliers(
        self, df: pd.DataFrame, column: str, outliers: pd.Series, options: DataCleaningOptions
    ) -> None:
        """Handle detected outliers in a column.
        
        Args:
            df: DataFrame to modify (in-place)
            column: Column name
            outliers: Boolean series indicating outliers
            options: Options for handling outliers
        """
        outlier_count = outliers.sum()
        self.logger.info(f"Found {outlier_count} outliers in column '{column}'")
        
        if options.outlier_action == "remove":
            # Mark rows for removal (will be removed later)
            df.loc[outliers, "_outlier_remove_"] = True
        elif options.outlier_action == "replace":
            # Replace outliers with median
            median_value = df[column].median()
            df.loc[outliers, column] = median_value
        elif options.outlier_action == "flag":
            # Add a flag column
            flag_col = f"{column}_outlier"
            df[flag_col] = outliers
            
    def _convert_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert data types in a DataFrame.
        
        Args:
            df: DataFrame to modify
            
        Returns:
            Modified DataFrame
        """
        self.logger.info("Converting data types")
        
        # Use pandas' convert_dtypes to infer better data types
        result = df.convert_dtypes()
        
        # Try to convert object columns to numeric if possible
        for col in result.select_dtypes(include=['object']).columns:
            try:
                # Try to convert to numeric
                numeric_series = pd.to_numeric(result[col], errors='coerce')
                
                # If conversion was successful (not too many NaNs), use it
                if numeric_series.isna().sum() / len(numeric_series) < 0.5:
                    result[col] = numeric_series
            except:
                pass
                
        return result
        
    def _clean_text_columns(self, df: pd.DataFrame, options: DataCleaningOptions) -> pd.DataFrame:
        """Clean text columns in a DataFrame.
        
        Args:
            df: DataFrame to modify
            options: Options for text cleaning
            
        Returns:
            Modified DataFrame
        """
        result = df.copy()
        
        # Process string/object columns
        text_cols = result.select_dtypes(include=['object', 'string']).columns
        
        if len(text_cols) == 0:
            self.logger.info("No text columns found for cleaning")
            return result
            
        self.logger.info(f"Cleaning {len(text_cols)} text columns")
        
        for col in text_cols:
            # Skip columns that are all NaN
            if result[col].isna().all():
                continue
                
            # Apply text cleaning operations
            if options.remove_html:
                result[col] = result[col].apply(
                    lambda x: re.sub(r'<.*?>', '', str(x)) if pd.notna(x) else x
                )
                
            if options.remove_urls:
                result[col] = result[col].apply(
                    lambda x: re.sub(r'https?://\S+|www\.\S+', '', str(x)) if pd.notna(x) else x
                )
                
            if options.remove_special_chars:
                result[col] = result[col].apply(
                    lambda x: re.sub(r'[^\w\s]', '', str(x)) if pd.notna(x) else x
                )
                
            if options.lowercase:
                result[col] = result[col].apply(
                    lambda x: str(x).lower() if pd.notna(x) else x
                )
                
        return result
        
    def _remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove duplicate rows from a DataFrame.
        
        Args:
            df: DataFrame to modify
            subset: Columns to consider for identifying duplicates
            
        Returns:
            Modified DataFrame
        """
        # Ensure subset columns exist in the DataFrame
        if subset:
            subset = [col for col in subset if col in df.columns]
            
        # Count duplicates before removal
        if subset:
            dup_count = df.duplicated(subset=subset).sum()
        else:
            dup_count = df.duplicated().sum()
            
        if dup_count > 0:
            self.logger.info(f"Removing {dup_count} duplicate rows")
            return df.drop_duplicates(subset=subset, keep='first')
        else:
            self.logger.info("No duplicate rows found")
            return df
            
    def _apply_custom_transformations(
        self, df: pd.DataFrame, transformations: Dict[str, Callable[[pd.Series], pd.Series]]
    ) -> pd.DataFrame:
        """Apply custom transformations to columns.
        
        Args:
            df: DataFrame to modify
            transformations: Dictionary mapping column names to transformation functions
            
        Returns:
            Modified DataFrame
        """
        result = df.copy()
        
        for col, transform_func in transformations.items():
            if col in result.columns:
                self.logger.info(f"Applying custom transformation to column '{col}'")
                try:
                    result[col] = transform_func(result[col])
                except Exception as e:
                    self.logger.error(f"Error applying transformation to column '{col}': {e}")
                    
        return result
