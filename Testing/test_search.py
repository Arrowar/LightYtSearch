"""
Test script for LightYtSearch functionality.
This file tests that the basic YouTube search feature works correctly.
"""

import sys
import os
import unittest
from datetime import datetime

# Fix path for importing the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LightYtSearch import search_youtube
from LightYtSearch.version import __version__


class TestYouTubeSearch(unittest.TestCase):
    """Test cases for YouTube search functionality."""

    def test_basic_search(self):
        """Test that a basic search returns results."""
        results = search_youtube("python tutorial", max_results=3, verbose=False, showResults=False)
        self.assertIsNotNone(results, "Search returned None")
        self.assertIsInstance(results, list, "Results should be a list")
        self.assertGreaterEqual(len(results), 1, "At least one result should be returned")

    def test_result_structure(self):
        """Test that search results have the expected structure."""
        results = search_youtube("programming", max_results=2, verbose=False, showResults=False)
        
        if not results:
            self.skipTest("No results returned, cannot test structure")
            
        # Check first result has required fields
        result = results[0]
        self.assertIn('type', result, "Result should have a 'type' field")
        self.assertIn('title', result, "Result should have a 'title' field")
        self.assertIn('url', result, "Result should have a 'url' field")
        
        # More specific tests based on result type
        if result['type'] == 'video':
            self.assertIn('channel', result, "Video result should have a 'channel' field")
            self.assertIn('views', result, "Video result should have a 'views' field")
            
        elif result['type'] == 'playlist':
            self.assertIn('channel', result, "Playlist result should have a 'channel' field")
            self.assertIn('video_count', result, "Playlist result should have a 'video_count' field")
            
        elif result['type'] == 'movie':
            self.assertIn('description', result, "Movie result should have a 'description' field")

    def test_filter_type(self):
        """Test that filter_type parameter works."""
        results = search_youtube("latest news", max_results=3, 
                                filter_type="video", verbose=False, showResults=False)
        
        if not results:
            self.skipTest("No results returned, cannot test filter")
            
        # All results should be videos
        for result in results:
            self.assertEqual(result['type'], 'video', 
                            f"Result should be a video but got {result['type']}")


def run_tests():
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestYouTubeSearch))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    print(f"Running tests for LightYtSearch v{__version__}")
    print(f"Date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = run_tests()
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())