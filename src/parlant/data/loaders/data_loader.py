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

"""Data loaders for various file formats."""

import os
import json
import csv
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from parlant.core.loggers import Logger


class DataFormat(str, Enum):
    """Supported data formats."""
    
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PARQUET = "parquet"
    SQL = "sql"
    TEXT = "text"
    XML = "xml"
    HTML = "html"
    YAML = "yaml"
    UNKNOWN = "unknown"


@dataclass
class DataLoaderOptions:
    """Options for data loading."""
    
    # General options
    encoding: str = "utf-8"
    header: bool = True
    skip_rows: int = 0
    max_rows: Optional[int] = None
    
    # CSV options
    delimiter: str = ","
    quotechar: str = '"'
    
    # Excel options
    sheet_name: Union[str, int] = 0
    
    # JSON options
    orient: str = "records"
    lines: bool = False
    
    # SQL options
    query: Optional[str] = None
    connection_string: Optional[str] = None
    
    # Parquet options
    columns: Optional[List[str]] = None
    
    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)


class DataLoader:
    """Data loader for various file formats."""
    
    def __init__(self, logger: Logger):
        """Initialize the data loader.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def detect_format(self, file_path: str) -> DataFormat:
        """Detect the format of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected format
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        
        if ext == "csv":
            return DataFormat.CSV
        elif ext in ["json", "jsonl"]:
            return DataFormat.JSON
        elif ext in ["xls", "xlsx", "xlsm"]:
            return DataFormat.EXCEL
        elif ext == "parquet":
            return DataFormat.PARQUET
        elif ext in ["sql", "sqlite", "db"]:
            return DataFormat.SQL
        elif ext == "txt":
            return DataFormat.TEXT
        elif ext == "xml":
            return DataFormat.XML
        elif ext in ["html", "htm"]:
            return DataFormat.HTML
        elif ext in ["yaml", "yml"]:
            return DataFormat.YAML
        else:
            return DataFormat.UNKNOWN
            
    def load_file(self, file_path: str, options: Optional[DataLoaderOptions] = None) -> pd.DataFrame:
        """Load data from a file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
            
        Raises:
            ValueError: If the file format is not supported
            FileNotFoundError: If the file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if options is None:
            options = DataLoaderOptions()
            
        # Detect the format if not specified
        format_type = self.detect_format(file_path)
        
        self.logger.info(f"Loading {format_type} file: {file_path}")
        
        if format_type == DataFormat.CSV:
            return self._load_csv(file_path, options)
        elif format_type == DataFormat.JSON:
            return self._load_json(file_path, options)
        elif format_type == DataFormat.EXCEL:
            return self._load_excel(file_path, options)
        elif format_type == DataFormat.PARQUET:
            return self._load_parquet(file_path, options)
        elif format_type == DataFormat.SQL:
            return self._load_sql(file_path, options)
        elif format_type == DataFormat.TEXT:
            return self._load_text(file_path, options)
        elif format_type == DataFormat.XML:
            return self._load_xml(file_path, options)
        elif format_type == DataFormat.HTML:
            return self._load_html(file_path, options)
        elif format_type == DataFormat.YAML:
            return self._load_yaml(file_path, options)
        else:
            raise ValueError(f"Unsupported file format: {format_type}")
            
    def _load_csv(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a CSV file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            return pd.read_csv(
                file_path,
                encoding=options.encoding,
                header=0 if options.header else None,
                skiprows=options.skip_rows,
                nrows=options.max_rows,
                delimiter=options.delimiter,
                quotechar=options.quotechar,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise
            
    def _load_json(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a JSON file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            return pd.read_json(
                file_path,
                encoding=options.encoding,
                orient=options.orient,
                lines=options.lines,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading JSON file: {e}")
            raise
            
    def _load_excel(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from an Excel file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            return pd.read_excel(
                file_path,
                sheet_name=options.sheet_name,
                header=0 if options.header else None,
                skiprows=options.skip_rows,
                nrows=options.max_rows,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading Excel file: {e}")
            raise
            
    def _load_parquet(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a Parquet file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            return pd.read_parquet(
                file_path,
                columns=options.columns,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading Parquet file: {e}")
            raise
            
    def _load_sql(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a SQL database.
        
        Args:
            file_path: Path to the database file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        if not options.query:
            raise ValueError("SQL query is required for loading SQL data")
            
        try:
            connection_string = options.connection_string or f"sqlite:///{file_path}"
            return pd.read_sql(
                options.query,
                connection_string,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading SQL data: {e}")
            raise
            
    def _load_text(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a text file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            with open(file_path, "r", encoding=options.encoding) as f:
                lines = f.readlines()
                
            # Skip rows if needed
            if options.skip_rows > 0:
                lines = lines[options.skip_rows:]
                
            # Limit rows if needed
            if options.max_rows is not None:
                lines = lines[:options.max_rows]
                
            # Create a DataFrame with a single column
            return pd.DataFrame({"text": [line.strip() for line in lines]})
        except Exception as e:
            self.logger.error(f"Error loading text file: {e}")
            raise
            
    def _load_xml(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from an XML file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            return pd.read_xml(
                file_path,
                encoding=options.encoding,
                **options.custom_options,
            )
        except Exception as e:
            self.logger.error(f"Error loading XML file: {e}")
            raise
            
    def _load_html(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from an HTML file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            # Read HTML tables from the file
            tables = pd.read_html(
                file_path,
                encoding=options.encoding,
                header=0 if options.header else None,
                skiprows=options.skip_rows,
                **options.custom_options,
            )
            
            # Return the first table by default
            if tables:
                return tables[0]
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error loading HTML file: {e}")
            raise
            
    def _load_yaml(self, file_path: str, options: DataLoaderOptions) -> pd.DataFrame:
        """Load data from a YAML file.
        
        Args:
            file_path: Path to the file
            options: Options for loading
            
        Returns:
            Loaded data as a pandas DataFrame
        """
        try:
            import yaml
            
            with open(file_path, "r", encoding=options.encoding) as f:
                data = yaml.safe_load(f)
                
            # Convert to DataFrame
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                return pd.DataFrame({"data": [data]})
        except Exception as e:
            self.logger.error(f"Error loading YAML file: {e}")
            raise
