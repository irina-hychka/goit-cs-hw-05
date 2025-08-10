"""
MapReduce Word Frequency Analyzer

- Downloads text from a given URL.
- Splits the text into chunks for parallel processing (Map phase).
- Groups intermediate results (Shuffle & Sort phase).
- Aggregates word counts (Reduce phase).
- Visualizes the top N most frequent words in a horizontal bar chart.
"""

from __future__ import annotations

import re
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


class MapReduce:
    """Simple MapReduce implementation for word frequency analysis."""

    def __init__(self, num_mappers: int = 4, num_reducers: int = 2) -> None:
        self.num_mappers = num_mappers
        self.num_reducers = num_reducers

    @staticmethod
    def _map(text_chunk: str) -> List[Tuple[str, int]]:
        """Map phase: Extract words and emit (word, 1) pairs."""
        words = re.findall(r"\b\w+\b", text_chunk.lower())
        return [(word, 1) for word in words]

    @staticmethod
    def _shuffle_and_sort(mapped_values: List[Tuple[str, int]]) -> Dict[str, List[int]]:
        """Shuffle & Sort phase: Group values by key."""
        shuffled: Dict[str, List[int]] = defaultdict(list)
        for key, value in mapped_values:
            shuffled[key].append(value)
        return shuffled

    @staticmethod
    def _reduce(key: str, values: List[int]) -> Tuple[str, int]:
        """Reduce phase: Sum values for a given key."""
        return key, sum(values)

    def run(self, text: str) -> Dict[str, int]:
        """Run MapReduce on the given text."""
        # Split text into chunks for mappers
        chunk_size = max(1, (len(text) + self.num_mappers - 1) // self.num_mappers)
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

        # Map phase (parallel)
        mapped_results: List[Tuple[str, int]] = []
        with ThreadPoolExecutor(max_workers=self.num_mappers) as mapper_pool:
            for result in mapper_pool.map(self._map, chunks):
                mapped_results.extend(result)

        # Shuffle & Sort phase
        shuffled_data = self._shuffle_and_sort(mapped_results)

        # Assign keys to reducers
        reducer_assignments: Dict[int, List[str]] = defaultdict(list)
        for i, key in enumerate(shuffled_data.keys()):
            reducer_assignments[i % self.num_reducers].append(key)

        # Reduce phase (parallel)
        reduced_results: Dict[str, int] = {}
        with ThreadPoolExecutor(max_workers=self.num_reducers) as reducer_pool:
            futures = []
            for reducer_id, keys in reducer_assignments.items():
                for key in keys:
                    futures.append(
                        reducer_pool.submit(self._reduce, key, shuffled_data[key])
                    )
            for future in futures:
                k, v = future.result()
                reduced_results[k] = v

        return reduced_results


def fetch_text_from_url(url: str) -> str:
    """Download text content from a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] Failed to download text from {url}: {exc}")
        return ""


def visualize_top_words(word_counts: Dict[str, int], top_n: int = 10) -> None:
    """Display the top N words in a horizontal bar chart."""
    sorted_words = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
    top_words = sorted_words[:top_n]

    words = [word for word, _ in top_words]
    counts = [count for _, count in top_words]

    plt.figure(figsize=(10, 6))
    plt.barh(words[::-1], counts[::-1], color="skyblue")
    plt.xlabel("Frequency")
    plt.ylabel("Word")
    plt.title(f"Top {top_n} Most Frequent Words")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Example URL
    url = "https://raw.githubusercontent.com/dscape/spell/master/test/resources/big.txt"

    print(f"[INFO] Downloading text from {url}...")
    text_data = fetch_text_from_url(url)

    if text_data:
        print("[INFO] Running MapReduce word frequency analysis...")
        mr = MapReduce(num_mappers=4, num_reducers=2)
        frequencies = mr.run(text_data)

        print("[INFO] Visualization...")
        visualize_top_words(frequencies, top_n=10)
    else:
        print("[WARN] No text to analyze.")
