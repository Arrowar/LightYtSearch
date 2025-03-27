# LightYtSearch

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/LightYtSearch.svg)](https://pypi.org/project/LightYtSearch/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Downloads](https://img.shields.io/pypi/dm/LightYtSearch.svg)](https://pypi.org/project/LightYtSearch/)
[![Commits](https://img.shields.io/github/commit-activity/m/Arrowar/LightYtSearch)](https://github.com/Arrowar/LightYtSearch/commits/main)
[![Last Commit](https://img.shields.io/github/last-commit/Arrowar/LightYtSearch)](https://github.com/Arrowar/LightYtSearch/commits/main)

</div>

A lightweight Python package to search YouTube without using the official API.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [As a Python Module](#as-a-python-module)
  - [Function Parameters](#function-parameters)
  - [Command-line Interface](#command-line-interface)
  - [CLI Arguments](#cli-arguments)
- [Data Structure](#data-structure)
  - [Video Results](#video-results)
  - [Playlist Results](#playlist-results)
  - [Movie Results](#movie-results)
- [Examples](#examples)
- [Limitations](#limitations)
- [Acknowledgments](#acknowledgments)

## Features

- Search for videos, playlists, and movies on YouTube
- Extract detailed information including titles, channels, view counts, and more
- No API key required
- Colorful command-line interface
- JSON output support
- Configurable search parameters (language, region, etc.)
- Fault-tolerant with retry capabilities

## Installation

Install from PyPI using pip:

```bash
pip install LightYtSearch
```

Or install the development version from GitHub:

```bash
pip install git+https://github.com/Arrowar/LightYtSearch.git
```

## Quick Start

```python
from LightYtSearch import search_youtube

# Basic search
results = search_youtube("python tutorial", max_results=5)
print(f"Found {len(results)} results")

# Print titles and URLs
for item in results:
    print(f"{item['type']}: {item['title']}")
    print(f"URL: {item['url']}")
    print("---")
```

## Usage

### As a Python Module

```python
from LightYtSearch import search_youtube

# Search for "python tutorial" and get up to 5 results
results = search_youtube("python tutorial", max_results=5)

# Process the results
for item in results:
    print(f"{item['type']}: {item['title']}")
    print(f"URL: {item['url']}")
    print("---")
```

### Function Parameters

The `search_youtube()` function accepts the following parameters:

- `query` (str): The search term to look for on YouTube.
- `max_results` (int, optional): Maximum number of results to return. Default is 5. **Note: The maximum possible value is 20 due to YouTube's page limitations.**
- `filter_type` (str, optional): Filter results by type. Accepted values: 'video', 'playlist', 'movie'. Default is None (all types).
- `timeout` (int, optional): Request timeout in seconds. Default is 10.
- `language` (str, optional): Language code for search results. Default is 'en'.
- `region` (str, optional): Region code for search results. Default is 'US'.
- `save_json` (bool, optional): Whether to save results to a JSON file. Default is False.
- `output_file` (str, optional): Path to save results JSON. Default is 'results.json'.
- `verbose` (bool, optional): Whether to print progress and results to console. Default is True.
- `showResults` (bool, optional): Whether to display search results in terminal. Default is True.
- `retry_count` (int, optional): Number of retries if request fails. Default is 3.
- `retry_delay` (int, optional): Delay between retries in seconds. Default is 2.

### Command-line Interface

```bash
# Basic search
LightYtSearch "python tutorial"

# Get 10 results (maximum is 20)
LightYtSearch "python tutorial" -n 10

# Export to JSON
LightYtSearch "python tutorial" -j > results.json

# Save to a file
LightYtSearch "python tutorial" -s -o my_results.json

# Filter by type
LightYtSearch "python tutorial" --filter video

# Set custom timeout, language, and region
LightYtSearch "python tutorial" --timeout 15 --language fr --region FR

# Configure retry behavior
LightYtSearch "python tutorial" --retry-count 5 --retry-delay 3
```

### CLI Arguments

- `query`: Search term (required)
- `-n, --max-results`: Maximum number of results (default: 5, max: 20)
- `-j, --json`: Output results as JSON
- `-s, --save`: Save results to a file
- `-o, --output`: Output filename (default: results.json)
- `-q, --quiet`: Quiet mode (minimal output)
- `-v, --version`: Show version information
- `--filter`: Filter results by type (video, playlist, movie)
- `--timeout`: Request timeout in seconds (default: 10)
- `--language`: Language code (default: en)
- `--region`: Region code (default: US)
- `--retry-count`: Number of retries for failed requests (default: 3)
- `--retry-delay`: Delay between retries in seconds (default: 2)

## Data Structure

The function returns a list of dictionaries with different structures depending on the item type:

### Video Results
```python
{
    'type': 'video',
    'id': 'video_id',
    'title': 'Video title',
    'channel': {
        'name': 'Channel name',
        'id': 'channel_id',
        'url': 'https://www.youtube.com/channel/channel_id',
        'thumbnail': 'Channel thumbnail URL',
        'badges': ['Verified', 'Official Artist', etc.]
    },
    'views': {
        'full': '1,234,567 views',
        'short': '1.2M views'
    },
    'published': '2 years ago',
    'duration': '12:34',
    'description': 'Video description snippet',
    'thumbnails': [thumbnail objects],
    'rich_thumbnail': 'Moving thumbnail URL',
    'flags': {
        'is_live': False,
        'is_upcoming': False,
        'has_closed_captions': True
    },
    'upcoming_date': None,
    'overlay_icons': ['4K', 'HD', etc.],
    'url': 'https://www.youtube.com/watch?v=video_id'
}
```

### Playlist Results
```python
{
    'type': 'playlist',
    'id': 'playlist_id',
    'title': 'Playlist title',
    'channel': {
        'name': 'Channel name',
        'id': 'channel_id',
        'url': 'https://www.youtube.com/channel/channel_id'
    },
    'video_count': '42 videos',
    'thumbnails': [thumbnail objects],
    'video_previews': [
        {
            'title': 'Video title',
            'id': 'video_id',
            'url': 'https://www.youtube.com/watch?v=video_id'
        }
    ],
    'url': 'https://www.youtube.com/playlist?list=playlist_id'
}
```

### Movie Results
```python
{
    'type': 'movie',
    'id': 'movie_id',
    'title': 'Movie title',
    'description': 'Movie description',
    'duration': '1:23:45',
    'publisher': 'Studio name',
    'metadata': ['2023', 'PG-13', etc.],
    'bottom_metadata': ['Adventure', 'Action', etc.],
    'thumbnails': [thumbnail objects],
    'is_vertical_poster': False,
    'badges': ['4K', 'HD', etc.],
    'offers': ['Rent $3.99', 'Buy $14.99', etc.],
    'url': 'https://www.youtube.com/watch?v=movie_id'
}
```

## Examples

### Searching for Videos Only

```python
from LightYtSearch import search_youtube

# Search for videos only
videos = search_youtube("python programming", filter_type="video", max_results=10)
for video in videos:
    print(f"Title: {video['title']}")
    print(f"Channel: {video['channel']['name']}")
    print(f"Views: {video['views']['full']}")
    print(f"Duration: {video['duration']}")
    print(f"URL: {video['url']}")
    print("---")
```

### Saving Results to a JSON File

```python
from LightYtSearch import search_youtube

# Search and save to custom file
search_youtube("machine learning", max_results=15, save_json=True, output_file="ml_videos.json")
```

### Using Different Region and Language

```python
from LightYtSearch import search_youtube

# Search in Italian from Italy
results_it = search_youtube("ricette pasta", language="it", region="IT", max_results=5)

# Search in Spanish from Mexico
results_es = search_youtube("recetas mexicanas", language="es", region="MX", max_results=5)
```

## Limitations

- **Maximum Results**: This library can extract a maximum of 20 results per search query due to YouTube's initial page load limitations.
- **No Pagination**: Currently doesn't support fetching more than the initial results page.
- **Subject to Changes**: YouTube's HTML structure might change, which could affect the scraping functionality.
- **Rate Limiting**: Excessive use might trigger YouTube's rate limiting mechanisms.
- **No Official Support**: This is not using the official YouTube API and is therefore not officially supported by YouTube.

## Acknowledgments

- Inspired by the need for a lightweight YouTube search solution without API key requirements
- Thanks to all contributors who have helped shape this project
- This library is for educational purposes and personal use
