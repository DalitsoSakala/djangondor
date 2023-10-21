from pathlib import Path
from django.db.models import QuerySet
from typing import Dict

def export_data_as_excel(data:list[list]|QuerySet,renamed_columns:Dict=None,index=False,column_header:list|bool=True,sheet_name='Sheet1'):
    
    from django.conf import settings
    import pandas as pd
    import tempfile as tf
    
    directory=Path(settings.MEDIA_ROOT)/'exports'
    frame = pd.DataFrame.from_records(data) if len(list(data)) else pd.DataFrame.from_dict({
            k:[''] for k in column_header
        })

    if renamed_columns and not column_header:
        frame.rename(columns=renamed_columns,inplace=True)
    
    
    file=tf.NamedTemporaryFile('w+b',dir=directory,suffix='.xlsx',delete=False)
    writer=pd.ExcelWriter(file.name)
    frame.to_excel(writer,index=index,header=column_header if column_header else None,sheet_name=sheet_name)
    
    for column in frame:
        column_length = max(frame[column].astype(str).map(len).max(), len(column))
        col_idx = frame.columns.get_loc(column)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length)
    writer.close()
    return file