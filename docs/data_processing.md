# Data Processing and Analysis

This document describes the data processing and analysis functionality in the Parlant framework.

## Overview

The data processing and analysis module provides a comprehensive set of tools for working with data, including:

1. Data loading from various formats
2. Data preprocessing and cleaning
3. Tabular data analysis
4. Data visualization
5. Machine learning integration

## Components

### Data Loading

The `DataLoader` class provides functionality for loading data from various file formats:

- CSV
- JSON
- Excel
- Parquet
- SQL
- Text
- XML
- HTML
- YAML

Example usage:

```python
from parlant.data import DataLoader, DataLoaderOptions
from parlant.core.loggers import ConsoleLogger

# Create a data loader
loader = DataLoader(ConsoleLogger())

# Configure options
options = DataLoaderOptions(
    encoding="utf-8",
    header=True,
    skip_rows=0,
    max_rows=None,
    delimiter=",",
)

# Load data from a CSV file
df = loader.load_file("data.csv", options)
```

### Data Preprocessing

The `DataCleaner` class provides functionality for cleaning and preprocessing data:

- Handling missing values
- Detecting and handling outliers
- Converting data types
- Cleaning text data
- Removing duplicates

Example usage:

```python
from parlant.data import DataCleaner, DataCleaningOptions
from parlant.core.loggers import ConsoleLogger

# Create a data cleaner
cleaner = DataCleaner(ConsoleLogger())

# Configure options
options = DataCleaningOptions(
    handle_missing=True,
    imputation_strategy="mean",
    handle_outliers=True,
    outlier_method="z_score",
    outlier_threshold=3.0,
    convert_dtypes=True,
    clean_text=True,
    remove_duplicates=True,
)

# Clean data
cleaned_df = cleaner.clean_data(df, options)
```

### Data Analysis

The `DataAnalyzer` class provides functionality for analyzing tabular data:

- Descriptive statistics
- Correlation analysis
- Feature importance

Example usage:

```python
from parlant.data import DataAnalyzer, DataAnalysisOptions
from parlant.core.loggers import ConsoleLogger

# Create a data analyzer
analyzer = DataAnalyzer(ConsoleLogger())

# Configure options
options = DataAnalysisOptions(
    include_numeric=True,
    include_categorical=True,
    correlation_method="pearson",
    correlation_min_value=0.3,
    target_column="target",
    feature_importance_method="random_forest",
)

# Analyze data
analysis = analyzer.analyze_data(df, options)

# Access analysis results
print(f"Data shape: {analysis['shape']}")
print(f"Missing values: {analysis['missing_values']['total_missing']}")
print(f"Numeric statistics: {analysis['numeric_stats']}")
print(f"Categorical statistics: {analysis['categorical_stats']}")
print(f"Correlation: {analysis['correlation']}")
print(f"Feature importance: {analysis['feature_importance']}")
```

### Data Visualization

The `DataVisualizer` class provides functionality for creating visualizations from tabular data:

- Bar charts
- Line charts
- Scatter plots
- Pie charts
- Histograms
- Box plots
- Violin plots
- Heatmaps
- Pair plots
- Joint plots

Example usage:

```python
from parlant.data import DataVisualizer, VisualizationOptions, ChartType
from parlant.core.loggers import ConsoleLogger

# Create a data visualizer
visualizer = DataVisualizer(ConsoleLogger())

# Configure options
options = VisualizationOptions(
    title="Age Distribution",
    x_label="Age",
    y_label="Count",
    figsize=(10, 6),
    palette="viridis",
    grid=True,
    legend=True,
)

# Create a bar chart
chart = visualizer.create_visualization(
    df,
    ChartType.BAR,
    x="age_group",
    y="count",
    options=options,
)

# The chart is returned as a base64-encoded image
# You can display it in a web interface or save it to a file
```

### Machine Learning

The `ModelTrainer` class provides functionality for training and evaluating machine learning models:

- Classification
- Regression
- Clustering
- Model evaluation
- Feature importance
- Model saving and loading

Example usage:

```python
from parlant.data import ModelTrainer, ModelTrainingOptions, ModelType
from parlant.core.loggers import ConsoleLogger

# Create a model trainer
trainer = ModelTrainer(ConsoleLogger())

# Configure options
options = ModelTrainingOptions(
    test_size=0.2,
    random_state=42,
    handle_categorical=True,
    handle_missing=True,
    normalize=True,
    cross_validation=True,
    n_folds=5,
)

# Train a classification model
model_result = trainer.train_model(
    df,
    target_column="target",
    model_type=ModelType.RANDOM_FOREST,
    options=options,
)

# Access model and evaluation results
print(f"Model type: {model_result['model_type']}")
print(f"Is classifier: {model_result['is_classifier']}")
print(f"Feature names: {model_result['feature_names']}")
print(f"Evaluation: {model_result['evaluation']}")
print(f"Feature importance: {model_result['feature_importance']}")

# Make predictions
predictions = trainer.predict(model_result, new_data)

# Save the model
trainer.save_model(model_result, "model.pkl")

# Load the model
loaded_model = trainer.load_model("model.pkl")
```

## Integration with Parlant

The data processing and analysis functionality is integrated with the Parlant framework:

1. **Agent Tools**: The data processing components can be used as tools for agents
2. **UI Components**: The visualization components can be used in the UI
3. **Analysis**: The data analysis components can be used for analyzing agent behavior
4. **Machine Learning**: The machine learning components can be used for enhancing agent capabilities

## Dependencies

The data processing and analysis module depends on the following libraries:

- pandas: For data manipulation
- numpy: For numerical operations
- matplotlib: For creating visualizations
- seaborn: For enhanced visualizations
- scikit-learn: For machine learning
- kneed: For finding optimal number of clusters

## Future Enhancements

Potential future enhancements for the data processing and analysis module:

1. **Natural Language Queries**: Add support for querying data using natural language
2. **Automated Machine Learning**: Add support for automated model selection and hyperparameter tuning
3. **Time Series Analysis**: Add support for time series data analysis and forecasting
4. **Deep Learning Integration**: Add support for deep learning models
5. **Interactive Visualizations**: Add support for interactive visualizations
