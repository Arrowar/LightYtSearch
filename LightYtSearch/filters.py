"""
Filtering and display functionality for YouTube search results.
Contains functions for extracting and displaying specific content types.
"""

from typing import List, Dict, Any, Optional
from .utils import colors

def extract_search_results(data: Dict[str, Any], query: str, max_results: int = 5, 
                          filter_type: Optional[str] = None, verbose: bool = True, 
                          showResults: bool = True) -> List[Dict[str, Any]]:
    """
    Extract and process search results from YouTube data
    
    Args:
        data (dict): YouTube initial data
        query (str): Original search query
        max_results (int): Maximum number of results to process
        filter_type (str, optional): Filter by content type ('video', 'playlist', 'movie')
        verbose (bool): Whether to print information during extraction
        showResults (bool): Whether to display the search results in the terminal
    
    Returns:
        list: Processed search results
    """
    processed_results = []
    
    # Get the contents dictionary from the initial data
    contents = data.get('contents', {})
    if not contents:
        if verbose:
            print(f"{colors.fg.red}No content found in the response data{colors.reset}")
        return processed_results

    items = []
    possible_paths = [

        # Path 1: Standard search results path
        lambda d: d.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {})
                   .get('sectionListRenderer', {}).get('contents', []),
        
        # Path 2: Alternative path used in some response formats
        lambda d: d.get('contents', {}).get('sectionListRenderer', {}).get('contents', []),
        
        # Path 3: Tab-based structure
        lambda d: d.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])[0]
                   .get('tabRenderer', {}).get('content', {}).get('sectionListRenderer', {}).get('contents', []),
                   
        # Path 4: Direct item section path
        lambda d: d.get('itemSectionRenderer', {}).get('contents', []),
        
        # Path 5: Direct rich grid renderer
        lambda d: d.get('contents', {}).get('richGridRenderer', {}).get('contents', [])
    ]
    
    section_contents = []
    
    # Try each path to find the section contents
    for path_func in possible_paths:
        try:
            result = path_func(data)
            if result:
                section_contents = result
                if verbose:
                    print(f"{colors.fg.green}Found items using path {possible_paths.index(path_func) + 1}{colors.reset}")
                break
        except (KeyError, IndexError, TypeError):
            continue
    
    # Extract items from section contents
    for section in section_contents:
        if 'itemSectionRenderer' in section:
            items_list = section.get('itemSectionRenderer', {}).get('contents', [])
            if items_list:
                items.extend(items_list)
                if verbose:
                    print(f"{colors.fg.green}Found {len(items_list)} items in section{colors.reset}")

        elif 'continuationItemRenderer' in section:
            if verbose:
                print(f"{colors.fg.yellow}Found continuation section (more results available){colors.reset}")

        elif 'richItemRenderer' in section:
            rich_item = section.get('richItemRenderer', {}).get('content', {})
            if rich_item:
                items.append(rich_item)
                if verbose and len(items) <= 5:
                    print(f"{colors.fg.green}Found item in richItemRenderer{colors.reset}")
    
    # Additional fallback for direct item section
    if not items and 'items' in data:
        items = data.get('items', [])
        if verbose and items:
            print(f"{colors.fg.green}Found {len(items)} items in direct items field{colors.reset}")
    
    if not items:
        if verbose:
            print(f"{colors.fg.red}No items found in search results after trying multiple paths{colors.reset}")
            print("Please check the structure in output.json to identify the correct path")
        return processed_results
    
    # Process each item to extract information
    count = 0
    for item in items:
        if 'infoPanelContainerRenderer' in item or 'adSlotRenderer' in item:
            continue
            
        # Process video result - standard renderer
        if 'videoRenderer' in item and (not filter_type or filter_type.lower() == 'video'):
            video_data = item['videoRenderer']
            video_info = extract_video_info(video_data)
            if video_info:
                processed_results.append(video_info)
                count += 1
                if verbose and showResults:
                    display_video_info(video_info)
        
        # Process video with context renderer (new YouTube format)
        elif 'videoWithContextRenderer' in item and (not filter_type or filter_type.lower() == 'video'):
            video_data = item['videoWithContextRenderer']
            video_info = extract_video_info(video_data)
            if video_info:
                processed_results.append(video_info)
                count += 1
                if verbose and showResults:
                    display_video_info(video_info)
                    
        # Process horizontal card renderer (used for some video types)
        elif 'horizontalCardRenderer' in item and (not filter_type or filter_type.lower() == 'video'):

            # Extract video from horizontal card if available
            card_data = item['horizontalCardRenderer']
            if 'videoWithContextRenderer' in card_data:
                video_data = card_data['videoWithContextRenderer']
                video_info = extract_video_info(video_data)
                if video_info:
                    processed_results.append(video_info)
                    count += 1
                    if verbose and showResults:
                        display_video_info(video_info)
        
        # Process movie result
        elif 'movieRenderer' in item and (not filter_type or filter_type.lower() == 'movie'):
            movie_data = item['movieRenderer']
            movie_info = extract_movie_info(movie_data)
            if movie_info:
                processed_results.append(movie_info)
                count += 1
                if verbose and showResults:
                    display_movie_info(movie_info)
        
        # Process playlist result
        elif 'playlistRenderer' in item and (not filter_type or filter_type.lower() == 'playlist'):
            playlist_data = item['playlistRenderer']
            playlist_info = extract_playlist_info(playlist_data)
            if playlist_info:
                processed_results.append(playlist_info)
                count += 1
                if verbose and showResults:
                    display_playlist_info(playlist_info)
        
        # Handle compact video renderer format
        elif 'compactVideoRenderer' in item and (not filter_type or filter_type.lower() == 'video'):
            video_data = item['compactVideoRenderer']
            video_info = extract_video_info(video_data)
            if video_info:
                processed_results.append(video_info)
                count += 1
                if verbose and showResults:
                    display_video_info(video_info)
                
        if max_results > 0 and count >= max_results:
            break
    
    if verbose:
        print(f"\n{colors.fg.green}Found {colors.bold}{len(processed_results)}{colors.reset}{colors.fg.green} results for query: '{colors.fg.yellow}{query}{colors.fg.green}'{colors.reset}")
        if count == 0:
            print(f"{colors.fg.yellow}No matching results were found. Check output.json for the actual response structure.{colors.reset}")
        elif max_results > len(processed_results) and max_results > 20:
            print(f"{colors.fg.orange}Note: Only {len(processed_results)} results were found instead of the requested {max_results}.{colors.reset}")
    
    return processed_results

def extract_video_info(video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract detailed information from a video renderer object"""
    try:
        if 'videoWithContextRenderer' in video_data:
            video_data = video_data['videoWithContextRenderer']
            
        video_id = video_data.get('videoId', 'N/A')
        if video_id == 'N/A':
            if 'navigationEndpoint' in video_data:
                nav = video_data['navigationEndpoint']
                if 'watchEndpoint' in nav:
                    video_id = nav['watchEndpoint'].get('videoId', 'N/A')
        
        # Improved title extraction with multiple fallbacks
        title = 'N/A'
        if 'title' in video_data:
            # Method 1: Extract from runs array
            if 'runs' in video_data['title'] and video_data['title']['runs']:
                runs_text = [run.get('text', '') for run in video_data['title']['runs']]
                title = ''.join(runs_text)
            
            # Method 2: Extract from simpleText
            elif 'simpleText' in video_data['title']:
                title = video_data['title']['simpleText']
            
            # Method 3: Extract from accessibility label
            elif 'accessibility' in video_data['title'] and 'accessibilityData' in video_data['title']['accessibility']:
                access_label = video_data['title']['accessibility']['accessibilityData'].get('label', '')
                if access_label:
                    # Sometimes the accessibility label includes " by [channel name]" and other info
                    if ' by ' in access_label:
                        title = access_label.split(' by ')[0]
                    else:
                        title = access_label
        
        # Additional fallback for title in headline field (some mobile responses)
        if title == 'N/A' and 'headline' in video_data:
            if 'runs' in video_data['headline'] and video_data['headline']['runs']:
                runs_text = [run.get('text', '') for run in video_data['headline']['runs']]
                title = ''.join(runs_text)
            elif 'simpleText' in video_data['headline']:
                title = video_data['headline']['simpleText']
        
        # Extract channel information
        channel_name = 'N/A'
        channel_id = 'N/A'
        
        # Check different field names for channel info
        channel_fields = [
            'ownerText', 'shortBylineText', 'longBylineText', 'channelTitleText'
        ]
        
        for field in channel_fields:
            if field in video_data:
                if 'runs' in video_data[field]:
                    channel_name = video_data[field]['runs'][0]['text']
                    if 'navigationEndpoint' in video_data[field]['runs'][0]:
                        nav_endpoint = video_data[field]['runs'][0]['navigationEndpoint']
                        if 'browseEndpoint' in nav_endpoint and 'browseId' in nav_endpoint['browseEndpoint']:
                            channel_id = nav_endpoint['browseEndpoint']['browseId']
                    break
                elif 'simpleText' in video_data[field]:
                    channel_name = video_data[field]['simpleText']
                    break
            
        # Extract view count
        view_count = 'N/A'
        short_view_count = 'N/A'
        
        # Try different field names for view count
        view_fields = ['viewCountText', 'viewCount']
        for field in view_fields:
            if field in video_data:
                if 'simpleText' in video_data[field]:
                    view_count = video_data[field]['simpleText']
                    break
                elif 'runs' in video_data[field]:
                    view_count = ''.join([run['text'] for run in video_data[field]['runs']])
                    break
        
        # Try different field names for short view count
        short_view_fields = ['shortViewCountText', 'shortFormViewCount']
        for field in short_view_fields:
            if field in video_data:
                if 'simpleText' in video_data[field]:
                    short_view_count = video_data[field]['simpleText']
                    break
                elif 'runs' in video_data[field]:
                    short_view_count = ''.join([run['text'] for run in video_data[field]['runs']])
                    break
            
        # Extract published time
        published_time = 'N/A'
        pub_fields = ['publishedTimeText', 'dateText']
        for field in pub_fields:
            if field in video_data:
                if 'simpleText' in video_data[field]:
                    published_time = video_data[field]['simpleText']
                    break
                elif 'runs' in video_data[field]:
                    published_time = ''.join([run['text'] for run in video_data[field]['runs']])
                    break
            
        # Extract duration
        duration = 'N/A'
        duration_fields = ['lengthText', 'timeText', 'durationText']
        for field in duration_fields:
            if field in video_data:
                if 'simpleText' in video_data[field]:
                    duration = video_data[field]['simpleText']
                    break
                elif 'runs' in video_data[field]:
                    duration = ''.join([run['text'] for run in video_data[field]['runs']])
                    break
            
        # Check for badges (like "Verified", "Official Artist", etc.)
        badges = []
        if 'ownerBadges' in video_data:
            for badge in video_data['ownerBadges']:
                if 'metadataBadgeRenderer' in badge:
                    badge_text = badge['metadataBadgeRenderer'].get('style', '')
                    if 'tooltip' in badge['metadataBadgeRenderer']:
                        badge_text = badge['metadataBadgeRenderer']['tooltip']
                    badges.append(badge_text)
        
        # Extract thumbnail URLs
        thumbnails = []
        if 'thumbnail' in video_data and 'thumbnails' in video_data['thumbnail']:
            thumbnails = video_data['thumbnail']['thumbnails']
        
        # Extract detailed metadata snippets (video description preview)
        description_snippet = 'N/A'
        desc_fields = ['detailedMetadataSnippets', 'descriptionSnippet']
        
        for field in desc_fields:
            if field in video_data:
                if isinstance(video_data[field], list) and video_data[field]:
                    snippet = video_data[field][0]
                    if 'snippetText' in snippet and 'runs' in snippet['snippetText']:
                        description_snippet = ' '.join([run['text'] for run in snippet['snippetText']['runs']])
                        break
                elif 'runs' in video_data[field]:
                    description_snippet = ' '.join([run['text'] for run in video_data[field]['runs']])
                    break
        
        # Extract rich thumbnail information if available
        rich_thumbnail = None
        if 'richThumbnail' in video_data and 'movingThumbnailRenderer' in video_data['richThumbnail']:
            moving_renderer = video_data['richThumbnail']['movingThumbnailRenderer']

            if 'movingThumbnailDetails' in moving_renderer:
                rich_thumbnail = moving_renderer['movingThumbnailDetails'].get('thumbnails', [{}])[0].get('url')
            elif 'thumbnails' in moving_renderer:
                rich_thumbnail = moving_renderer['thumbnails'][0].get('url')
        
        # Check if video is a live stream
        is_live = False
        if 'badges' in video_data:
            for badge in video_data['badges']:
                if 'labelBadgeRenderer' in badge and badge['labelBadgeRenderer'].get('style') == 'BADGE_STYLE_TYPE_LIVE_NOW':
                    is_live = True
                    break
        
        # Alternative way to check for live status
        if 'thumbnailOverlays' in video_data:
            for overlay in video_data['thumbnailOverlays']:
                if 'thumbnailOverlayTimeStatusRenderer' in overlay:
                    style = overlay['thumbnailOverlayTimeStatusRenderer'].get('style', '')
                    if style == 'LIVE':
                        is_live = True
                        break
        
        # Get overlay icons (like 4K, HD, CC, etc.)
        overlay_icons = []
        if 'thumbnailOverlays' in video_data:
            for overlay in video_data['thumbnailOverlays']:
                if 'thumbnailOverlayTimeStatusRenderer' in overlay:
                    style = overlay['thumbnailOverlayTimeStatusRenderer'].get('style')
                    if style and style not in ['DEFAULT', 'LIVE']:
                        overlay_icons.append(style)
        
        # Check if video has closed captions
        has_closed_captions = False
        if 'thumbnailOverlays' in video_data:
            for overlay in video_data['thumbnailOverlays']:
                if 'thumbnailOverlayToggleButtonRenderer' in overlay:
                    toggle = overlay['thumbnailOverlayToggleButtonRenderer']
                    if 'toggledIcon' in toggle and toggle['toggledIcon'].get('iconType') == 'SUBTITLES':
                        has_closed_captions = True
                        break
        
        # Get channel thumbnail if available
        channel_thumbnail = None
        if 'channelThumbnailSupportedRenderers' in video_data:
            channel_renderer = video_data['channelThumbnailSupportedRenderers'].get('channelThumbnailWithLinkRenderer', {})
            if 'thumbnail' in channel_renderer and 'thumbnails' in channel_renderer['thumbnail']:
                channel_thumbnail = channel_renderer['thumbnail']['thumbnails'][-1].get('url')
                
        # Alternative way to get channel thumbnail
        elif 'channelThumbnail' in video_data and 'thumbnails' in video_data['channelThumbnail']:
            channel_thumbnail = video_data['channelThumbnail']['thumbnails'][-1].get('url')
        
        # Check if video is upcoming (premiere)
        is_upcoming = False
        upcoming_date = None
        if 'upcomingEventData' in video_data:
            is_upcoming = True
            upcoming_date = video_data['upcomingEventData'].get('startTime')
        
        # Construct video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id != 'N/A' else 'N/A'
        
        return {
            'type': 'video',
            'id': video_id,
            'title': title,
            'channel': {
                'name': channel_name,
                'id': channel_id,
                'url': channel_url,
                'thumbnail': channel_thumbnail,
                'badges': badges
            },
            'views': {
                'full': view_count,
                'short': short_view_count
            },
            'published': published_time,
            'duration': duration,
            'description': description_snippet,
            'thumbnails': thumbnails,
            'rich_thumbnail': rich_thumbnail,
            'flags': {
                'is_live': is_live,
                'is_upcoming': is_upcoming,
                'has_closed_captions': has_closed_captions
            },
            'upcoming_date': upcoming_date,
            'overlay_icons': overlay_icons,
            'url': video_url
        }
        
    except Exception as e:
        print(f"{colors.fg.red}Error extracting video info: {str(e)}{colors.reset}")
        return None

def extract_movie_info(movie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract detailed information from a movie renderer object"""
    try:
        movie_id = movie_data.get('videoId', 'N/A')
        
        # Extract title
        title = 'N/A'
        if 'title' in movie_data and 'runs' in movie_data['title']:
            title = movie_data['title']['runs'][0]['text']
        elif 'title' in movie_data and 'simpleText' in movie_data['title']:
            title = movie_data['title']['simpleText']
            
        # Extract description
        description = 'N/A'
        if 'descriptionSnippet' in movie_data and 'runs' in movie_data['descriptionSnippet']:
            description = ' '.join([run['text'] for run in movie_data['descriptionSnippet']['runs']])
            
        # Extract duration
        duration = 'N/A'
        if 'lengthText' in movie_data and 'simpleText' in movie_data['lengthText']:
            duration = movie_data['lengthText']['simpleText']
            
        # Extract metadata items
        metadata = []
        if 'topMetadataItems' in movie_data:
            for item in movie_data['topMetadataItems']:
                if 'simpleText' in item:
                    metadata.append(item['simpleText'])
                elif 'runs' in item:
                    metadata.append(' '.join([run['text'] for run in item['runs']]))
        
        # Extract bottom metadata items (like year, rating, genre)
        bottom_metadata = []
        if 'bottomMetadataItems' in movie_data:
            for item in movie_data['bottomMetadataItems']:
                if 'simpleText' in item:
                    bottom_metadata.append(item['simpleText'])
                elif 'runs' in item:
                    bottom_metadata.append(' '.join([run['text'] for run in item['runs']]))
        
        # Extract publisher/studio info
        publisher = 'N/A'
        if 'longBylineText' in movie_data and 'runs' in movie_data['longBylineText']:
            publisher = movie_data['longBylineText']['runs'][0]['text']
        
        # Extract thumbnail URLs
        thumbnails = []
        if 'thumbnail' in movie_data and 'thumbnails' in movie_data['thumbnail']:
            thumbnails = movie_data['thumbnail']['thumbnails']
        
        # Check if it uses vertical poster style
        is_vertical_poster = movie_data.get('useVerticalPoster', False)
        
        # Extract badges (like "4K", "HD", etc.)
        badges = []
        if 'badges' in movie_data:
            for badge in movie_data['badges']:
                if 'metadataBadgeRenderer' in badge:
                    badge_text = badge['metadataBadgeRenderer'].get('label', '')
                    badges.append(badge_text)
        
        # Extract pricing/offer info
        offers = []
        if 'offerButtons' in movie_data:
            for offer in movie_data['offerButtons']:
                if 'buttonRenderer' in offer:
                    button = offer['buttonRenderer']
                    offer_text = ' '.join([run['text'] for run in button.get('text', {}).get('runs', [])])
                    offers.append(offer_text)
        
        # Construct movie URL
        movie_url = f"https://www.youtube.com/watch?v={movie_id}"
        
        return {
            'type': 'movie',
            'id': movie_id,
            'title': title,
            'description': description,
            'duration': duration,
            'publisher': publisher,
            'metadata': metadata,
            'bottom_metadata': bottom_metadata,
            'thumbnails': thumbnails,
            'is_vertical_poster': is_vertical_poster,
            'badges': badges,
            'offers': offers,
            'url': movie_url
        }
        
    except Exception as e:
        print(f"{colors.fg.red}Error extracting movie info: {str(e)}{colors.reset}")
        return None

def extract_playlist_info(playlist_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract detailed information from a playlist renderer object"""
    try:
        playlist_id = playlist_data.get('playlistId', 'N/A')
        
        # Extract title
        title = 'N/A'
        if 'title' in playlist_data and 'runs' in playlist_data['title']:
            title = playlist_data['title']['runs'][0]['text']
        elif 'title' in playlist_data and 'simpleText' in playlist_data['title']:
            title = playlist_data['title']['simpleText']
            
        # Extract channel/owner information
        channel_name = 'N/A'
        channel_id = 'N/A'
        if 'longBylineText' in playlist_data and 'runs' in playlist_data['longBylineText']:
            channel_name = playlist_data['longBylineText']['runs'][0]['text']
            if 'navigationEndpoint' in playlist_data['longBylineText']['runs'][0]:
                nav_endpoint = playlist_data['longBylineText']['runs'][0]['navigationEndpoint']
                if 'browseEndpoint' in nav_endpoint and 'browseId' in nav_endpoint['browseEndpoint']:
                    channel_id = nav_endpoint['browseEndpoint']['browseId']
        
        # Extract video count
        video_count = 'N/A'
        if 'videoCount' in playlist_data and 'simpleText' in playlist_data['videoCount']:
            video_count = playlist_data['videoCount']['simpleText']
        elif 'videoCount' in playlist_data and 'runs' in playlist_data['videoCount']:
            video_count = ''.join([run['text'] for run in playlist_data['videoCount']['runs']])
        
        # Extract thumbnail URLs
        thumbnails = []
        if 'thumbnails' in playlist_data and playlist_data['thumbnails']:
            for thumbnail_set in playlist_data['thumbnails']:
                if 'thumbnails' in thumbnail_set:
                    thumbnails.extend(thumbnail_set['thumbnails'])
        
        # Extract video preview information
        video_previews = []
        if 'videos' in playlist_data:
            for video in playlist_data['videos']:
                if 'childVideoRenderer' in video:
                    video_renderer = video['childVideoRenderer']
                    video_title = 'N/A'

                    if 'title' in video_renderer and 'simpleText' in video_renderer['title']:
                        video_title = video_renderer['title']['simpleText']

                    video_id = video_renderer.get('videoId', 'N/A')
                    video_previews.append({
                        'title': video_title,
                        'id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
        
        # Construct playlist URL
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id != 'N/A' else 'N/A'
        
        return {
            'type': 'playlist',
            'id': playlist_id,
            'title': title,
            'channel': {
                'name': channel_name,
                'id': channel_id,
                'url': channel_url
            },
            'video_count': video_count,
            'thumbnails': thumbnails,
            'video_previews': video_previews,
            'url': playlist_url
        }
        
    except Exception as e:
        print(f"{colors.fg.red}Error extracting playlist info: {str(e)}{colors.reset}")
        return None


def display_video_info(video_info: Dict[str, Any]) -> None:
    """Display formatted video information"""
    print(f"{colors.fg.purple}{'-' * 60}{colors.reset}")
    print(f"{colors.fg.lightgrey}TYPE    : {colors.fg.lightcyan}{video_info['type'].upper()}{colors.reset}")
    print(f"{colors.fg.lightgrey}TITLE   : {colors.fg.lightgreen}{video_info['title']}{colors.reset}")
    print(f"{colors.fg.lightgrey}CHANNEL : {colors.fg.yellow}{video_info['channel']['name']}{colors.reset}")
    
    if video_info['channel']['badges']:
        print(f"{colors.fg.lightgrey}BADGES  : {colors.fg.orange}{', '.join(video_info['channel']['badges'])}{colors.reset}")
    
    print(f"{colors.fg.lightgrey}DURATION: {colors.fg.lightblue}{video_info['duration']}{colors.reset}")
    print(f"{colors.fg.lightgrey}VIEWS   : {colors.fg.cyan}{video_info['views']['full']}{colors.reset}")
    print(f"{colors.fg.lightgrey}UPLOADED: {colors.fg.cyan}{video_info['published']}{colors.reset}")
    
    if video_info['description'] != 'N/A':
        desc = video_info['description'][:100] + ('...' if len(video_info['description']) > 100 else '')
        print(f"{colors.fg.lightgrey}DESCR   : {colors.fg.lightcyan}{desc}{colors.reset}")
    
    if video_info['flags']['is_live']:
        print(f"{colors.fg.lightgrey}STATUS  : {colors.fg.red}LIVE NOW{colors.reset}")
    elif video_info['flags']['is_upcoming']:
        print(f"{colors.fg.lightgrey}STATUS  : {colors.fg.orange}UPCOMING (Start time: {video_info['upcoming_date']}){colors.reset}")
    
    if video_info['flags']['has_closed_captions']:
        print(f"{colors.fg.lightgrey}FEATURES: {colors.fg.yellow}Has closed captions{colors.reset}")
    
    if video_info['overlay_icons']:
        print(f"{colors.fg.lightgrey}QUALITY : {colors.fg.lightgreen}{', '.join(video_info['overlay_icons'])}{colors.reset}")
    
    print(f"{colors.fg.lightgrey}VIDEO   : {colors.fg.blue}{video_info['url']}{colors.reset}")
    print(f"{colors.fg.lightgrey}CHANNEL : {colors.fg.blue}{video_info['channel']['url']}{colors.reset}")
    
    if video_info['thumbnails']:
        print(f"{colors.fg.lightgrey}THUMB   : {colors.fg.blue}{video_info['thumbnails'][-1]['url']}{colors.reset}")

def display_movie_info(movie_info: Dict[str, Any]) -> None:
    """Display formatted movie information"""
    print(f"{colors.fg.purple}{'-' * 60}{colors.reset}")
    print(f"{colors.fg.lightgrey}TYPE    : {colors.fg.pink}{movie_info['type'].upper()}{colors.reset}")
    print(f"{colors.fg.lightgrey}TITLE   : {colors.fg.lightgreen}{movie_info['title']}{colors.reset}")
    print(f"{colors.fg.lightgrey}DURATION: {colors.fg.lightblue}{movie_info['duration']}{colors.reset}")
    
    if movie_info['publisher'] != 'N/A':
        print(f"{colors.fg.lightgrey}STUDIO  : {colors.fg.yellow}{movie_info['publisher']}{colors.reset}")
    
    if movie_info['description'] != 'N/A':
        desc = movie_info['description'][:100] + ('...' if len(movie_info['description']) > 100 else '')
        print(f"{colors.fg.lightgrey}DESCR   : {colors.fg.lightcyan}{desc}{colors.reset}")
    
    if movie_info['metadata']:
        print(f"{colors.fg.lightgrey}INFO    : {colors.fg.cyan}{' | '.join(movie_info['metadata'])}{colors.reset}")
    
    if movie_info['bottom_metadata']:
        print(f"{colors.fg.lightgrey}DETAILS : {colors.fg.cyan}{' | '.join(movie_info['bottom_metadata'])}{colors.reset}")
    
    if movie_info['badges']:
        print(f"{colors.fg.lightgrey}BADGES  : {colors.fg.orange}{', '.join(movie_info['badges'])}{colors.reset}")
    
    if movie_info['offers']:
        print(f"{colors.fg.lightgrey}OFFERS  : {colors.fg.green}{', '.join(movie_info['offers'])}{colors.reset}")
    
    print(f"{colors.fg.lightgrey}URL     : {colors.fg.blue}{movie_info['url']}{colors.reset}")
    
    if movie_info['thumbnails']:
        print(f"{colors.fg.lightgrey}THUMB   : {colors.fg.blue}{movie_info['thumbnails'][-1]['url']}{colors.reset}")
    
    if movie_info['is_vertical_poster']:
        print(f"{colors.fg.lightgrey}FORMAT  : {colors.fg.purple}Vertical Poster{colors.reset}")

def display_playlist_info(playlist_info: Dict[str, Any]) -> None:
    """Display formatted playlist information"""
    print(f"{colors.fg.purple}{'-' * 60}{colors.reset}")
    print(f"{colors.fg.lightgrey}TYPE      : {colors.fg.lightcyan}{playlist_info['type'].upper()}{colors.reset}")
    print(f"{colors.fg.lightgrey}TITLE     : {colors.fg.lightgreen}{playlist_info['title']}{colors.reset}")
    print(f"{colors.fg.lightgrey}CHANNEL   : {colors.fg.yellow}{playlist_info['channel']['name']}{colors.reset}")
    print(f"{colors.fg.lightgrey}VIDEOS    : {colors.fg.lightblue}{playlist_info['video_count']}{colors.reset}")
    
    # Show preview of videos in playlist (up to 3)
    if playlist_info['video_previews']:
        print(f"{colors.fg.lightgrey}INCLUDES  :{colors.reset}")
        for i, video in enumerate(playlist_info['video_previews'][:3]):
            print(f"{colors.fg.cyan}  - {colors.fg.lightgreen}{video['title']}{colors.reset}")
        if len(playlist_info['video_previews']) > 3:
            print(f"{colors.fg.cyan}  - ...and {colors.fg.yellow}{len(playlist_info['video_previews']) - 3}{colors.fg.cyan} more{colors.reset}")
    
    print(f"{colors.fg.lightgrey}URL       : {colors.fg.blue}{playlist_info['url']}{colors.reset}")
    print(f"{colors.fg.lightgrey}CHANNEL   : {colors.fg.blue}{playlist_info['channel']['url']}{colors.reset}")
    
    if playlist_info['thumbnails']:
        print(f"{colors.fg.lightgrey}THUMB     : {colors.fg.blue}{playlist_info['thumbnails'][-1]['url']}{colors.reset}")