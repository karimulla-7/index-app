"""
Database Query Optimization and Profiling Utility
Index Archival Suite — CSBS Utilities
"""

import time
import sqlite3
from typing import List, Dict, Any

class QueryOptimizer:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def explain_query_plan(self, query: str) -> List[Dict[str, Any]]:
        """Executes EXPLAIN QUERY PLAN to detect full table scans."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def benchmark_query(self, query: str, iterations: int = 100) -> float:
        """Measures average execution latency across benchmark iterations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            start = time.perf_counter()
            for _ in range(iterations):
                cursor.execute(query)
                cursor.fetchall()
            elapsed = time.perf_counter() - start
            return (elapsed / iterations) * 1000.0  # Milliseconds
