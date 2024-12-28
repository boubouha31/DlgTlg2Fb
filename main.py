import requests

# Telegram Bot API Configuration
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHANNELS = {
    1: '@channel1',  # Replace with Channel 1 username or ID
    2: '@channel2',  # Replace with Channel 2 username or ID
    3: '@channel3',  # Replace with Channel 3 username or ID
}

# Facebook Graph API Configuration
FACEBOOK_ACCESS_TOKEN = 'YOUR_FACEBOOK_ACCESS_TOKEN'
FACEBOOK_GROUPS = {
    1: 'group_id_1',  # Replace with Group ID for Channel 1
    2: 'group_id_2',  # Replace with Group ID for Channel 2
    3: 'group_id_3',  # Replace with Group ID for Channel 3
}

# API Endpoints
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com'


def get_telegram_updates():
    """Fetch updates from the Telegram bot."""
    response = requests.get(f"{TELEGRAM_API_URL}/getUpdates")
    if response.status_code == 200:
        return response.json().get('result', [])
    return []


def parse_telegram_message(message):
    """Parse Telegram messages and extract relevant content."""
    parsed_data = {
        'text': None,
        'photos': [],
        'videos': [],
        'poll': None,
    }

    if 'text' in message:
        parsed_data['text'] = message['text']

    if 'photo' in message:
        # Sort photos by file size to get the largest
        largest_photo = max(message['photo'], key=lambda x: x['file_size'])
        parsed_data['photos'].append(get_telegram_file_url(largest_photo['file_id']))

    if 'video' in message:
        parsed_data['videos'].append(get_telegram_file_url(message['video']['file_id']))

    if 'media_group_id' in message:
        # Handle albums (grouped photos/videos)
        parsed_data['album_id'] = message['media_group_id']

    if 'poll' in message:
        parsed_data['poll'] = message['poll']

    return parsed_data


def get_telegram_file_url(file_id):
    """Get the URL for a Telegram file."""
    response = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
    if response.status_code == 200:
        file_path = response.json()['result']['file_path']
        return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    return None


def post_to_facebook(group_id, content):
    """Post content to a Facebook group."""
    if 'text' in content and not content.get('photos') and not content.get('videos'):
        # Post text-only content
        payload = {
            'message': content['text'],
            'access_token': FACEBOOK_ACCESS_TOKEN,
        }
        response = requests.post(f"{FACEBOOK_GRAPH_API_URL}/{group_id}/feed", data=payload)
        return response.json()

    if content.get('photos'):
        # Post photos
        for photo_url in content['photos']:
            payload = {
                'url': photo_url,
                'caption': content.get('text', ''),
                'access_token': FACEBOOK_ACCESS_TOKEN,
            }
            response = requests.post(f"{FACEBOOK_GRAPH_API_URL}/{group_id}/photos", data=payload)
            print(response.json())

    if content.get('videos'):
        # Post videos
        for video_url in content['videos']:
            payload = {
                'file_url': video_url,
                'description': content.get('text', ''),
                'access_token': FACEBOOK_ACCESS_TOKEN,
            }
            response = requests.post(f"{FACEBOOK_GRAPH_API_URL}/{group_id}/videos", data=payload)
            print(response.json())

    if content.get('poll'):
        # Post poll link
        payload = {
            'message': f"Check out this poll on Telegram: {content['poll']}",
            'access_token': FACEBOOK_ACCESS_TOKEN,
        }
        response = requests.post(f"{FACEBOOK_GRAPH_API_URL}/{group_id}/feed", data=payload)
        return response.json()


def process_channels():
    """Fetch posts from Telegram channels and post them to Facebook groups."""
    updates = get_telegram_updates()
    for update in updates:
        if 'message' not in update:
            continue

        message = update['message']
        chat_id = message.get('chat', {}).get('username', None)

        # Match the chat ID with the corresponding Facebook group
        for channel_number, channel_id in TELEGRAM_CHANNELS.items():
            if chat_id == channel_id:
                content = parse_telegram_message(message)
                response = post_to_facebook(FACEBOOK_GROUPS[channel_number], content)
                print(f"Posted to Facebook Group {channel_number}: {response}")


if __name__ == "__main__":
    process_channels()