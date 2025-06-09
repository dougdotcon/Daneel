"""
Data visualization module for Daneel.

This module provides functionality for creating visualizations from tabular data,
including bar charts, line charts, scatter plots, and more.
"""

import base64
import io
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from Daneel.core.loggers import Logger


class ChartType(str, Enum):
    """Types of charts."""
    
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    PAIR = "pair"
    JOINT = "joint"


class ColorPalette(str, Enum):
    """Color palettes for charts."""
    
    DEFAULT = "default"
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    CIVIDIS = "cividis"
    BLUES = "Blues"
    GREENS = "Greens"
    REDS = "Reds"
    PURPLES = "Purples"
    ORANGES = "Oranges"
    GREYS = "Greys"


@dataclass
class VisualizationOptions:
    """Options for data visualization."""
    
    # General options
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    figsize: Tuple[int, int] = (10, 6)
    palette: ColorPalette = ColorPalette.DEFAULT
    
    # Chart-specific options
    bins: int = 10  # For histograms
    kind: str = "bar"  # For pandas plots
    stacked: bool = False  # For bar charts
    
    # Formatting options
    grid: bool = True
    legend: bool = True
    
    # Output options
    dpi: int = 100
    format: str = "png"
    
    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)


class DataVisualizer:
    """Data visualizer for creating charts and plots."""
    
    def __init__(self, logger: Logger):
        """Initialize the data visualizer.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def create_visualization(
        self, 
        df: pd.DataFrame, 
        chart_type: ChartType,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        options: Optional[VisualizationOptions] = None
    ) -> str:
        """Create a visualization from a DataFrame.
        
        Args:
            df: DataFrame to visualize
            chart_type: Type of chart to create
            x: Column to use for x-axis
            y: Column(s) to use for y-axis
            options: Visualization options
            
        Returns:
            Base64-encoded image data
        """
        if options is None:
            options = VisualizationOptions()
            
        self.logger.info(f"Creating {chart_type} visualization")
        
        # Create figure and axes
        plt.figure(figsize=options.figsize)
        
        # Set style
        sns.set_style("whitegrid" if options.grid else "white")
        
        # Set color palette
        if options.palette != ColorPalette.DEFAULT:
            sns.set_palette(options.palette)
            
        # Create the visualization based on chart type
        if chart_type == ChartType.BAR:
            self._create_bar_chart(df, x, y, options)
        elif chart_type == ChartType.LINE:
            self._create_line_chart(df, x, y, options)
        elif chart_type == ChartType.SCATTER:
            self._create_scatter_plot(df, x, y, options)
        elif chart_type == ChartType.PIE:
            self._create_pie_chart(df, x, y, options)
        elif chart_type == ChartType.HISTOGRAM:
            self._create_histogram(df, x, options)
        elif chart_type == ChartType.BOX:
            self._create_box_plot(df, x, y, options)
        elif chart_type == ChartType.VIOLIN:
            self._create_violin_plot(df, x, y, options)
        elif chart_type == ChartType.HEATMAP:
            self._create_heatmap(df, options)
        elif chart_type == ChartType.PAIR:
            self._create_pair_plot(df, options)
        elif chart_type == ChartType.JOINT:
            self._create_joint_plot(df, x, y, options)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
            
        # Set title and labels
        if options.title:
            plt.title(options.title)
            
        if options.x_label and x:
            plt.xlabel(options.x_label)
        elif x:
            plt.xlabel(x)
            
        if options.y_label and y and isinstance(y, str):
            plt.ylabel(options.y_label)
        elif y and isinstance(y, str):
            plt.ylabel(y)
            
        # Show legend if needed
        if options.legend:
            plt.legend()
            
        # Convert plot to image
        img_data = self._figure_to_base64(options.format, options.dpi)
        
        # Close the figure to free memory
        plt.close()
        
        return img_data
        
    def _create_bar_chart(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a bar chart.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for x-axis
            y: Column(s) to use for y-axis
            options: Visualization options
        """
        if x is None or y is None:
            raise ValueError("Both x and y must be specified for bar charts")
            
        if isinstance(y, list):
            # Multiple columns for y
            if options.stacked:
                df[y].plot(kind='bar', x=x, stacked=True)
            else:
                df[y].plot(kind='bar', x=x)
        else:
            # Single column for y
            sns.barplot(data=df, x=x, y=y)
            
    def _create_line_chart(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a line chart.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for x-axis
            y: Column(s) to use for y-axis
            options: Visualization options
        """
        if x is None or y is None:
            raise ValueError("Both x and y must be specified for line charts")
            
        if isinstance(y, list):
            # Multiple columns for y
            df.plot(kind='line', x=x, y=y)
        else:
            # Single column for y
            sns.lineplot(data=df, x=x, y=y)
            
    def _create_scatter_plot(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a scatter plot.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for x-axis
            y: Column to use for y-axis
            options: Visualization options
        """
        if x is None or y is None or isinstance(y, list):
            raise ValueError("Both x and y (single column) must be specified for scatter plots")
            
        hue = options.custom_options.get("hue")
        size = options.custom_options.get("size")
        
        sns.scatterplot(data=df, x=x, y=y, hue=hue, size=size)
            
    def _create_pie_chart(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a pie chart.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for labels
            y: Column to use for values
            options: Visualization options
        """
        if x is None or y is None or isinstance(y, list):
            raise ValueError("Both x and y (single column) must be specified for pie charts")
            
        # Group by x and sum y if needed
        if len(df) > 10:
            self.logger.info("Grouping data for pie chart")
            data = df.groupby(x)[y].sum()
        else:
            data = df.set_index(x)[y]
            
        data.plot(kind='pie', autopct='%1.1f%%')
            
    def _create_histogram(
        self, 
        df: pd.DataFrame, 
        x: Optional[str],
        options: VisualizationOptions
    ) -> None:
        """Create a histogram.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for values
            options: Visualization options
        """
        if x is None:
            raise ValueError("x must be specified for histograms")
            
        sns.histplot(data=df, x=x, bins=options.bins, kde=options.custom_options.get("kde", False))
            
    def _create_box_plot(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a box plot.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for categories
            y: Column to use for values
            options: Visualization options
        """
        if y is None or isinstance(y, list):
            raise ValueError("y (single column) must be specified for box plots")
            
        sns.boxplot(data=df, x=x, y=y)
            
    def _create_violin_plot(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a violin plot.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for categories
            y: Column to use for values
            options: Visualization options
        """
        if y is None or isinstance(y, list):
            raise ValueError("y (single column) must be specified for violin plots")
            
        sns.violinplot(data=df, x=x, y=y)
            
    def _create_heatmap(
        self, 
        df: pd.DataFrame,
        options: VisualizationOptions
    ) -> None:
        """Create a heatmap.
        
        Args:
            df: DataFrame to visualize (should be a correlation matrix)
            options: Visualization options
        """
        # Check if df is a correlation matrix, if not, create one
        if df.shape[0] != df.shape[1] or not all(df.columns == df.index):
            self.logger.info("Creating correlation matrix for heatmap")
            corr_method = options.custom_options.get("corr_method", "pearson")
            df = df.select_dtypes(include=["number"]).corr(method=corr_method)
            
        sns.heatmap(df, annot=options.custom_options.get("annot", True), cmap=options.custom_options.get("cmap", "coolwarm"))
            
    def _create_pair_plot(
        self, 
        df: pd.DataFrame,
        options: VisualizationOptions
    ) -> None:
        """Create a pair plot.
        
        Args:
            df: DataFrame to visualize
            options: Visualization options
        """
        # Limit to numeric columns
        numeric_df = df.select_dtypes(include=["number"])
        
        # Limit to at most 5 columns to avoid overcrowding
        if numeric_df.shape[1] > 5:
            self.logger.warning("Limiting pair plot to 5 columns")
            numeric_df = numeric_df.iloc[:, :5]
            
        hue = options.custom_options.get("hue")
        if hue and hue in df.columns:
            sns.pairplot(df, vars=numeric_df.columns, hue=hue)
        else:
            sns.pairplot(numeric_df)
            
    def _create_joint_plot(
        self, 
        df: pd.DataFrame, 
        x: Optional[str], 
        y: Optional[Union[str, List[str]]],
        options: VisualizationOptions
    ) -> None:
        """Create a joint plot.
        
        Args:
            df: DataFrame to visualize
            x: Column to use for x-axis
            y: Column to use for y-axis
            options: Visualization options
        """
        if x is None or y is None or isinstance(y, list):
            raise ValueError("Both x and y (single column) must be specified for joint plots")
            
        kind = options.custom_options.get("kind", "scatter")
        sns.jointplot(data=df, x=x, y=y, kind=kind)
            
    def _figure_to_base64(self, format: str = "png", dpi: int = 100) -> str:
        """Convert a matplotlib figure to base64-encoded image data.
        
        Args:
            format: Image format (png, jpg, svg, etc.)
            dpi: Image resolution
            
        Returns:
            Base64-encoded image data
        """
        buf = io.BytesIO()
        plt.savefig(buf, format=format, dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/{format};base64,{img_data}"
