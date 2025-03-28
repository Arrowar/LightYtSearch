"""
Simple example script for using the LightYtSearch package.
"""

import time
from LightYtSearch import search_youtube

def main():
    query = input("Enter a YouTube search query: ")
    results = search_youtube(query, max_results=5, showTimeExecution=True)

    print(f"\nFound {len(results)} results for '{query}'")

if __name__ == "__main__":
    main()