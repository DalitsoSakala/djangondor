import pandas as pd


def drop_tz_from_dataframe(df:pd.DataFrame):
    date_columns = df.select_dtypes(include=['datetime64[ns, UTC]']).columns
    for date_column in date_columns:
        df[date_column] = df[date_column].dt.tz_localize(None)