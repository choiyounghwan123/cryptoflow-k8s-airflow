import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CryptoDataPreprocessor:
    @staticmethod
    def preprocess_data(**context):
        try:
            raw_data = context['task_instance'].xcom_pull(task_ids='collect_crypto')

            if not raw_data or 'data' not in raw_data:
                raise ValueError("No valid crypto data found")
            
            df = pd.DataFrame(raw_data['data'])

            logger.info(f"Preprocessing {len(df)} crypto records")

            # 1. 데이터 타입 변환
            numeric_cols = ['rank', 'priceUsd', 'marketCapUsd', 'volumeUsd24Hr', 'changePercent24Hr']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 2. 문자열 정리
            if 'symbol' in df.columns:
                df['symbol'] = df['symbol'].str.upper().str.strip()
            
            # 3. 메타데이터 추가
            current_time = pd.Timestamp.now(tz='UTC')
            df['collected_at'] = current_time.isoformat()  # ISO format string으로 변환
            df['collection_date'] = current_time.date().isoformat()  # date를 string으로 변환
            df['collection_hour'] = current_time.hour

            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            raise