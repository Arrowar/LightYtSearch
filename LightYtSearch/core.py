"""
Core functionality for the YTSearch package.
Contains the main search_youtube function and helper functions.
"""

import os
import json
import httpx
import time
import random
import ua_generator
from typing import List, Dict, Any, Optional

from .utils import colors
from .extractors import YTInitialDataExtractor
from .filters import extract_search_results

def search_youtube(query: str, max_results: int = 5, filter_type: Optional[str] = None, 
                  timeout: int = 10, language: str = 'en', region: str = 'US', 
                  save_json: bool = False, output_file: Optional[str] = None, 
                  verbose: bool = False, showResults: bool = True, 
                  retry_count: int = 3, retry_delay: int = 2,
                  debug: bool = False, showTimeExecution: bool = False) -> List[Dict[str, Any]]: 
    """
    Search YouTube and extract detailed information from search results
    
    Args:
        query (str): The search query to use
        max_results (int): Maximum number of results to display (default: 5)
                          Note: YouTube initially loads about 20 results. To get more,
                          you would need to simulate scrolling or use YouTube's API.
        filter_type (str, optional): Filter results by type. Accepted values: 'video', 'playlist', 'movie'. Default is None (all types).
        timeout (int, optional): Request timeout in seconds. Default is 10.
        language (str, optional): Language code for search results. Default is 'en'.
        region (str, optional): Region code for search results. Default is 'US'.
        save_json (bool): Whether to save the results to a JSON file
        output_file (str): Path to save results JSON (if None, will use 'results.json')
        verbose (bool): Whether to print progress and results to console
        showResults (bool): Whether to display the search results in the terminal
        retry_count (int): Number of retries if request fails with 302 or other errors
        retry_delay (int): Delay between retries in seconds (with randomization)
        debug (bool): Enable additional debug output
        showTimeExecution (bool): Display execution time for each major process
    
    Returns:
        list: List of dictionaries containing video/movie information
    """
    # Start overall execution timer
    overall_start_time = time.time()
    
    if verbose:
        print(f"{colors.fg.purple}Searching YouTube for:{colors.reset} '{colors.bold}{query}{colors.reset}'")
        print(f"{colors.fg.purple}Retrieving up to {colors.fg.cyan}{max_results if max_results > 0 else 'all'}{colors.reset} results...")
        if max_results > 20:
            print(f"{colors.fg.warning}Note: YouTube typically loads only about 20 results initially. To get more results,{colors.reset}")
            print(f"{colors.fg.warning}you would need to simulate scrolling or use YouTube's official API.{colors.reset}")

    url = "https://www.youtube.com/results"
    params = {"search_query": query.strip().replace(" ", "+")}
    ua = ua_generator.generate(browser=('chrome', 'edge'))
    user_agent = ua.headers.get()['user-agent']
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': f"{language}-{region},en-US;q=0.9",
        'priority': 'u=0, i',
        'referer': 'https://www.google.com/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Opera";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'service-worker-navigation-preload': 'true',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }

    # Start HTTP request timer
    http_start_time = time.time()
    
    # Implement retries with exponential backoff
    response = None
    attempts = 0
    
    while attempts < retry_count:
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                response = client.get(url, params=params, headers=headers)
                if verbose:
                    print(f"{colors.fg.muted}Response status code: {colors.fg.cyan}{response.status_code}{colors.reset}")
                
                if verbose and attempts > 0:
                    print(f"{colors.fg.success}Request successful on attempt {colors.fg.highlight}{attempts+1}{colors.reset}")
                
                if response.status_code == 200:
                    break
                    
                if response.status_code == 302 or response.status_code >= 400:
                    if verbose:
                        print(f"{colors.fg.warning}Received status code {colors.fg.yellow}{response.status_code}{colors.fg.warning}, retrying...{colors.reset}")
                    
                    # Change user-agent
                    ua = ua_generator.generate(browser=('chrome', 'edge', 'firefox'))
                    headers['user-agent'] = ua.headers.get()['user-agent']
                    
                    if response.status_code == 302 and 'set-cookie' in response.headers:
                        headers['cookie'] = response.headers['set-cookie']

        except Exception as e:
            if verbose:
                print(f"{colors.fg.error}Error during request: {str(e)}{colors.reset}")
        
        # Increment attempts
        attempts += 1
        if attempts < retry_count:
            jitter = random.uniform(0.5, 1.5)
            delay = retry_delay * jitter * attempts

            if verbose:
                print(f"{colors.fg.amber}Waiting {colors.fg.yellow}{delay:.2f}s{colors.fg.amber} before retry {colors.fg.yellow}{attempts+1}/{retry_count}{colors.reset}")
            time.sleep(delay)
    
    http_execution_time = time.time() - http_start_time
    if showTimeExecution:
        print(f"\t{colors.fg.lightblue}HTTP Request: {colors.fg.yellow}{http_execution_time:.2f}s{colors.reset}")
    
    if not response or response.status_code != 200:
        if verbose:
            print(f"{colors.fg.error}Error retrieving the page. Status code: {colors.fg.red}{response.status_code if response else 'No response'}{colors.reset}")
        return []
    
    # Start data extraction timer
    extraction_start_time = time.time()
    
    # Get ytInitialData
    extractor = YTInitialDataExtractor(response.text)
    initial_data = extractor.extract()
    extraction_method = extractor.last_extraction_method
    
    extraction_execution_time = time.time() - extraction_start_time
    if showTimeExecution:
        print(f"\t{colors.fg.lightblue}Data Extraction: {colors.fg.yellow}{extraction_execution_time:.2f}s {colors.fg.lightgrey}(Method: {extraction_method}){colors.reset}")
    
    if not initial_data:
        if verbose:
            print(f"{colors.fg.error}Could not find initial data.{colors.reset}")
        return []
    
    # Save raw data when debug is enabled
    if debug:
        debug_file = os.path.join(os.getcwd(), 'debug_output.json')
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            if verbose:
                print(f"{colors.fg.success}Debug data saved to {colors.fg.info}{debug_file}{colors.reset}")
        except Exception as e:
            if verbose:
                print(f"{colors.fg.error}Error saving debug data: {str(e)}{colors.reset}")
    
    # Start processing timer
    processing_start_time = time.time()
    
    # Process the search results
    search_results = extract_search_results(initial_data, query, max_results, filter_type, verbose, showResults)
    
    processing_execution_time = time.time() - processing_start_time
    if showTimeExecution:
        print(f"\t{colors.fg.lightblue}Results Processing: {colors.fg.yellow}{processing_execution_time:.2f}s{colors.reset}")
    
    # Save results to JSON file if requested
    if save_json and search_results:
        saving_start_time = time.time()
        
        if output_file is None:
            output_file = os.path.join(os.getcwd(), 'output.json')
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(search_results, f, indent=2, ensure_ascii=False)
            
            saving_execution_time = time.time() - saving_start_time
            if showTimeExecution:
                print(f"\t{colors.fg.lightblue}Saving Results: {colors.fg.yellow}{saving_execution_time:.2f}s{colors.reset}")
                
            if verbose:
                print(f"{colors.fg.success}Results saved to {colors.fg.info}{output_file}{colors.reset}")
                
        except Exception as e:
            if verbose:
                print(f"{colors.fg.error}Error saving results to file: {str(e)}{colors.reset}")
    
    # Show total execution time
    overall_execution_time = time.time() - overall_start_time
    if showTimeExecution:
        print(f"\t{colors.fg.lightblue}{colors.bold}Total Execution: {colors.fg.yellow}{overall_execution_time:.2f}s{colors.reset}")
    
    return search_results