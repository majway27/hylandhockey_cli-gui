#!/usr/bin/env python3
"""
Data Processor
Handles CSV loading, cleaning, and validation of USA Hockey master registration data.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

from config.logging_config import get_logger

logger = get_logger(__name__)


class DataProcessorError(Exception):
    """Base exception for data processor errors."""
    pass


class DataProcessor:
    """Processes and cleans USA Hockey master registration data."""
    
    def __init__(self):
        """Initialize data processor."""
        self.logger = logger
        logger.info("DataProcessor initialized")
    
    def load_csv(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Load CSV file into a DataFrame.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Optional[pd.DataFrame]: Loaded DataFrame if successful, None otherwise
        """
        try:
            logger.info(f"Loading CSV file: {file_path}")
            
            # Try different encoding options
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
                    logger.info(f"Successfully loaded CSV with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    logger.warning(f"Failed to load with encoding: {encoding}")
                    continue
                except Exception as e:
                    logger.warning(f"Error loading with encoding {encoding}: {e}")
                    continue
            
            if df is None:
                logger.error("Failed to load CSV with any encoding")
                return None
            
            logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return None
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate the master registration data.
        
        Args:
            df: Raw DataFrame from CSV
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        try:
            logger.info("Starting data cleaning process...")
            
            # Make a copy to avoid modifying the original
            df_clean = df.copy()
            
            # Remove completely empty rows
            initial_rows = len(df_clean)
            df_clean = df_clean.dropna(how='all')
            if len(df_clean) < initial_rows:
                logger.info(f"Removed {initial_rows - len(df_clean)} completely empty rows")
            
            # Clean column names
            df_clean.columns = self._clean_column_names(df_clean.columns)
            
            # Standardize common fields
            df_clean = self._standardize_fields(df_clean)
            
            # Remove duplicates
            initial_rows = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            if len(df_clean) < initial_rows:
                logger.info(f"Removed {initial_rows - len(df_clean)} duplicate rows")
            
            # Validate required fields
            df_clean = self._validate_required_fields(df_clean)
            
            logger.info(f"Data cleaning completed. Final dataset: {len(df_clean)} records")
            return df_clean
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return df  # Return original if cleaning fails
    
    def _clean_column_names(self, columns: pd.Index) -> List[str]:
        """
        Clean column names for consistency.
        
        Args:
            columns: Original column names
            
        Returns:
            List[str]: Cleaned column names
        """
        cleaned_columns = []
        
        for col in columns:
            # Convert to string if not already
            col_str = str(col)
            
            # Remove extra whitespace
            col_str = col_str.strip()
            
            # Replace spaces with underscores
            col_str = col_str.replace(' ', '_')
            
            # Remove special characters except underscores
            col_str = re.sub(r'[^a-zA-Z0-9_]', '', col_str)
            
            # Convert to lowercase
            col_str = col_str.lower()
            
            # Handle empty column names
            if not col_str:
                col_str = f"unnamed_column_{len(cleaned_columns)}"
            
            # Handle duplicate column names
            if col_str in cleaned_columns:
                col_str = f"{col_str}_{cleaned_columns.count(col_str) + 1}"
            
            cleaned_columns.append(col_str)
        
        return cleaned_columns
    
    def _standardize_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize common fields in the dataset.
        
        Args:
            df: DataFrame to standardize
            
        Returns:
            pd.DataFrame: Standardized DataFrame
        """
        try:
            # Standardize name fields
            name_columns = [col for col in df.columns if 'name' in col.lower()]
            for col in name_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.title()
            
            # Standardize email fields
            email_columns = [col for col in df.columns if 'email' in col.lower()]
            for col in email_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.lower()
            
            # Standardize phone fields
            phone_columns = [col for col in df.columns if 'phone' in col.lower()]
            for col in phone_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).apply(self._standardize_phone)
            
            # Standardize date fields
            date_columns = [col for col in df.columns if 'date' in col.lower() or 'birth' in col.lower()]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Standardize jersey number fields
            jersey_columns = [col for col in df.columns if 'jersey' in col.lower() and 'number' in col.lower()]
            for col in jersey_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            logger.info("Field standardization completed")
            return df
            
        except Exception as e:
            logger.error(f"Error standardizing fields: {e}")
            return df
    
    def _standardize_phone(self, phone: str) -> str:
        """
        Standardize phone number format.
        
        Args:
            phone: Phone number string
            
        Returns:
            str: Standardized phone number
        """
        if pd.isna(phone) or phone == 'nan':
            return ''
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(phone))
        
        # Format based on length
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(phone).strip()
    
    def _validate_required_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and handle required fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            pd.DataFrame: Validated DataFrame
        """
        try:
            # Check for required fields (customize based on your needs)
            required_fields = []
            
            # Add validation logic here based on your requirements
            # For example:
            # if 'player_name' in df.columns:
            #     df = df[df['player_name'].notna()]
            
            logger.info("Field validation completed")
            return df
            
        except Exception as e:
            logger.error(f"Error validating fields: {e}")
            return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the dataset.
        
        Args:
            df: DataFrame to summarize
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            if df is None or df.empty:
                return {
                    "total_records": 0,
                    "columns": [],
                    "summary": "No data available"
                }
            
            summary = {
                "total_records": len(df),
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
                "unique_values": {},
                "numeric_summary": {},
                "categorical_summary": {}
            }
            
            # Add unique value counts for categorical columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    summary["unique_values"][col] = df[col].nunique()
                    summary["categorical_summary"][col] = {
                        "unique_count": df[col].nunique(),
                        "most_common": df[col].value_counts().head(5).to_dict()
                    }
            
            # Add numeric summaries
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                summary["numeric_summary"][col] = {
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "std": df[col].std()
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating data summary: {e}")
            return {
                "total_records": 0,
                "columns": [],
                "summary": f"Error generating summary: {str(e)}"
            }
    
    def filter_data(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter data based on specified criteria.
        
        Args:
            df: DataFrame to filter
            filters: Dictionary of filter criteria
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        try:
            df_filtered = df.copy()
            
            for column, value in filters.items():
                if column in df_filtered.columns:
                    if isinstance(value, (list, tuple)):
                        df_filtered = df_filtered[df_filtered[column].isin(value)]
                    else:
                        df_filtered = df_filtered[df_filtered[column] == value]
            
            logger.info(f"Data filtered: {len(df)} -> {len(df_filtered)} records")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error filtering data: {e}")
            return df
    
    def export_sample(self, df: pd.DataFrame, output_path: Path, sample_size: int = 100) -> bool:
        """
        Export a sample of the data for review.
        
        Args:
            df: DataFrame to sample
            output_path: Path for the output file
            sample_size: Number of records to include in sample
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Take a sample
            sample_df = df.sample(n=min(sample_size, len(df)), random_state=42)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on file extension
            if output_path.suffix.lower() == '.csv':
                sample_df.to_csv(output_path, index=False)
            elif output_path.suffix.lower() in ['.xlsx', '.xls']:
                sample_df.to_excel(output_path, index=False, engine='openpyxl')
            else:
                sample_df.to_csv(output_path, index=False)
            
            logger.info(f"Sample exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting sample: {e}")
            return False 