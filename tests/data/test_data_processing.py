"""
Tests for the data processing and analysis functionality.
"""

import os
import pytest
import pandas as pd
import numpy as np
import tempfile
from unittest.mock import MagicMock

from parlant.core.loggers import ConsoleLogger
from parlant.data.loaders import DataLoader, DataLoaderOptions, DataFormat
from parlant.data.preprocessing import DataCleaner, DataCleaningOptions
from parlant.data.analysis import DataAnalyzer, DataAnalysisOptions
from parlant.data.visualization import DataVisualizer, VisualizationOptions, ChartType
from parlant.data.ml import ModelTrainer, ModelTrainingOptions, ModelType


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    data = {
        "id": range(1, 101),
        "age": np.random.randint(18, 65, 100),
        "income": np.random.normal(50000, 15000, 100),
        "education": np.random.choice(["High School", "Bachelor", "Master", "PhD"], 100),
        "satisfaction": np.random.randint(1, 6, 100),
        "churn": np.random.choice([0, 1], 100, p=[0.8, 0.2]),
    }
    
    # Add some missing values
    df = pd.DataFrame(data)
    df.loc[np.random.choice(df.index, 10), "age"] = np.nan
    df.loc[np.random.choice(df.index, 10), "income"] = np.nan
    df.loc[np.random.choice(df.index, 10), "education"] = np.nan
    
    return df


@pytest.fixture
def sample_csv_file(sample_data):
    """Create a sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        sample_data.to_csv(f.name, index=False)
        return f.name


def test_data_loader(logger, sample_csv_file):
    """Test the DataLoader class."""
    # Create a data loader
    loader = DataLoader(logger)
    
    # Test format detection
    assert loader.detect_format(sample_csv_file) == DataFormat.CSV
    
    # Test loading data
    options = DataLoaderOptions(header=True)
    df = loader.load_file(sample_csv_file, options)
    
    # Check that the data was loaded correctly
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "id" in df.columns
    assert "age" in df.columns
    assert "income" in df.columns
    assert "education" in df.columns
    assert "satisfaction" in df.columns
    assert "churn" in df.columns
    
    # Clean up
    os.unlink(sample_csv_file)


def test_data_cleaner(logger, sample_data):
    """Test the DataCleaner class."""
    # Create a data cleaner
    cleaner = DataCleaner(logger)
    
    # Test cleaning data with default options
    options = DataCleaningOptions()
    cleaned_df = cleaner.clean_data(sample_data, options)
    
    # Check that missing values were handled
    assert cleaned_df["age"].isna().sum() == 0
    assert cleaned_df["income"].isna().sum() == 0
    assert cleaned_df["education"].isna().sum() == 0
    
    # Test with custom options
    options = DataCleaningOptions(
        handle_missing=True,
        handle_outliers=True,
        outlier_method="z_score",
        outlier_threshold=3.0,
        clean_text=True,
        lowercase=True,
    )
    cleaned_df = cleaner.clean_data(sample_data, options)
    
    # Check that the data was cleaned correctly
    assert cleaned_df.shape[0] == sample_data.shape[0]
    assert cleaned_df.shape[1] == sample_data.shape[1]


def test_data_analyzer(logger, sample_data):
    """Test the DataAnalyzer class."""
    # Create a data analyzer
    analyzer = DataAnalyzer(logger)
    
    # Test analyzing data with default options
    options = DataAnalysisOptions()
    analysis = analyzer.analyze_data(sample_data, options)
    
    # Check that the analysis contains the expected keys
    assert "shape" in analysis
    assert "columns" in analysis
    assert "dtypes" in analysis
    assert "missing_values" in analysis
    assert "numeric_stats" in analysis
    assert "categorical_stats" in analysis
    assert "correlation" in analysis
    
    # Check that the shape is correct
    assert analysis["shape"] == sample_data.shape
    
    # Check that numeric stats include expected columns
    assert "age" in analysis["numeric_stats"]
    assert "income" in analysis["numeric_stats"]
    assert "satisfaction" in analysis["numeric_stats"]
    
    # Check that categorical stats include expected columns
    assert "education" in analysis["categorical_stats"]


def test_data_visualizer(logger, sample_data):
    """Test the DataVisualizer class."""
    # Create a data visualizer
    visualizer = DataVisualizer(logger)
    
    # Test creating a bar chart
    options = VisualizationOptions(
        title="Age Distribution",
        x_label="Age",
        y_label="Count",
    )
    chart = visualizer.create_visualization(
        sample_data,
        ChartType.BAR,
        x="education",
        y="satisfaction",
        options=options,
    )
    
    # Check that the chart is a base64-encoded string
    assert isinstance(chart, str)
    assert chart.startswith("data:image/png;base64,")
    
    # Test creating a scatter plot
    options = VisualizationOptions(
        title="Income vs. Age",
        x_label="Age",
        y_label="Income",
    )
    chart = visualizer.create_visualization(
        sample_data,
        ChartType.SCATTER,
        x="age",
        y="income",
        options=options,
    )
    
    # Check that the chart is a base64-encoded string
    assert isinstance(chart, str)
    assert chart.startswith("data:image/png;base64,")


def test_model_trainer(logger, sample_data):
    """Test the ModelTrainer class."""
    # Skip if sklearn is not available
    pytest.importorskip("sklearn")
    
    # Create a model trainer
    trainer = ModelTrainer(logger)
    
    # Test training a classification model
    options = ModelTrainingOptions(
        test_size=0.2,
        random_state=42,
        handle_categorical=True,
        handle_missing=True,
        normalize=True,
    )
    
    # Fill missing values for this test
    test_data = sample_data.copy()
    test_data["age"] = test_data["age"].fillna(test_data["age"].mean())
    test_data["income"] = test_data["income"].fillna(test_data["income"].mean())
    test_data["education"] = test_data["education"].fillna(test_data["education"].mode()[0])
    
    model_result = trainer.train_model(
        test_data,
        target_column="churn",
        model_type=ModelType.RANDOM_FOREST,
        options=options,
    )
    
    # Check that the model result contains the expected keys
    assert "model" in model_result
    assert "model_type" in model_result
    assert "is_classifier" in model_result
    assert "feature_names" in model_result
    assert "evaluation" in model_result
    
    # Check that the model is a classifier
    assert model_result["is_classifier"] is True
    
    # Test making predictions
    predictions = trainer.predict(model_result, test_data)
    assert len(predictions) == len(test_data)
    
    # Test saving and loading the model
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        trainer.save_model(model_result, f.name)
        loaded_model = trainer.load_model(f.name)
        
        # Check that the loaded model contains the expected keys
        assert "model" in loaded_model
        assert "model_type" in loaded_model
        assert "is_classifier" in loaded_model
        
        # Clean up
        os.unlink(f.name)
        metadata_path = f"{os.path.splitext(f.name)[0]}_metadata.json"
        if os.path.exists(metadata_path):
            os.unlink(metadata_path)
