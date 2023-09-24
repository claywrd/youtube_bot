import os
import time
import logging
import threading
import sqlite3
import telebot

from datetime import datetime, timedelta
from googleapiclient.discovery import build
from dotenv import load_dotenv



load_dotenv()

#Provide the following values to the .env file
API_KEY =  os.getenv('API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')


# Logging system settings:
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Initialize the Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

#@bot.message_handler(commands=['start', 'help'])
#def send_welcome(message):
    #bot.reply_to(message, "Welcome to the YouTube Stats Bot! I will send you video statistics once an hour.")

# Initialize the YouTube Data API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Initialize an SQLite database
db_path = 'pp_video_stats.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create a table to store video information and statistics
cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        title TEXT,
        published_at DATETIME,
        views INTEGER,
        likes INTEGER,
        comments INTEGER,
        is_new INTEGER,
        stats_collected INTEGER
    )
''')
conn.commit()
conn.close()


# Get the list of videos from the channel
def read_videos(CHANNEL_ID):
    request = youtube.search().list(
            channelId=CHANNEL_ID,
            order='date',
            type='video',
            part='snippet',  # Include snippet information (which contains titles)
            maxResults=10)  # Adjust the number of results as needed
            
    latest_videos = request.execute()
    #print(latest_videos)
    return latest_videos


def new_video_add(latest_videos):

    # Extract video information and check for new videos
    for item in latest_videos['items']:
        video_id = item['id']['videoId']
        published_at_str = item['snippet']['publishedAt']
        title = item['snippet']['title']

        # Convert published_at to DATE data type
        #print(published_at_str)
        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
        #print(published_at)

        #Connect to DB
        db_path = 'pp_video_stats.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the video is already in the database
        cursor.execute('SELECT COUNT(*) FROM videos WHERE video_id = ?', (video_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            # Video is not in the database, add it
            cursor.execute('''
                INSERT INTO videos (video_id, title, published_at, views, likes, comments, is_new, stats_collected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (video_id, title, published_at, 0, 0, 0, 1, 0))
            conn.commit()
            print(f"New video found: {title} (ID: {video_id})")
        
        # Close DB connection
        conn.commit()
        conn.close()


def check_video_status(TELEGRAM_CHANNEL_ID):

    #Connect to DB
    db_path = 'pp_video_stats.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Collect statistics for new videos after an hour
    # Select new videos, waiting for an hour
    cursor.execute('SELECT * FROM videos WHERE stats_collected = 0 AND is_new =1')
    for row in cursor.fetchall():
        video_id, title, published_at, views, likes, comments, is_new, stats_collected = row

        now = datetime.utcnow()
        published_at_datetime = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
        time_since_published = now - published_at_datetime
        #Print info about videos in the queu for debug purposes. Can be removed in production
        print(f'There is a new video in the queu: {title}, ID: {video_id} Published at: {published_at} Time since published: {time_since_published}')

        #Check, if it's time to collect video statistics.
        if  time_since_published >= timedelta(hours=1.0):
            request = youtube.videos().list(
                    part='statistics, contentDetails',
                    id=video_id,) 
            video_stats = request.execute()

            stats = video_stats['items'][0]['statistics']
            try: 
                views = int(stats['viewCount'])
            except KeyError:
                views = 0

            likes = int(stats['likeCount'])
            comments = int(stats['commentCount'])

            #Duration should only be available for fully published videos. May be used to skip announcements and live streams.
            duration = video_stats['items'][0]['contentDetails']['duration']
            print(f'Duration: {duration}')
            #Check if video views is positive, else it is not ready for statistics collection
            if views > 0: 
                #Print statistics for debug purposes       
                print(f'Video: {title}')
                print(f'Video ID: {video_id}')
                print(f'Views: {views}')
                print(f'Likes: {likes}')
                print(f'Comments: {comments}')
                print(f'Published at: {published_at_datetime.strftime("%H:%M")} UTC')
                print(f'Time since published: {time_since_published.seconds // 3600} hour(s) {(time_since_published.seconds % 3600) // 60} minute(s) {time_since_published.days} days')
                print('------')

                # Send statistics to Telegram
                message = (
                    f'Video: {title}\n' 
                    f'Video ID: {video_id}\n'
                    f'Views: {views}\n'
                    f'Likes: {likes}\n'
                    f'Comments: {comments}\n'
                    f'Published at: {published_at_datetime.strftime("%H:%M")} UTC\n'
                    f'Time since published: {time_since_published.seconds // 3600} hour(s) {(time_since_published.seconds % 3600) // 60} minute(s)  {time_since_published.days} days \n'
                )
                bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
                time.sleep(1)

            

                # Update the statistics in the database
                cursor.execute('''
                    UPDATE videos 
                    SET views = ?, likes = ?, comments = ?, is_new = 0, stats_collected = 1 
                    WHERE video_id = ?
                    ''', (views, likes, comments, video_id))
                conn.commit()
                #Print for debug purposes. Can be removed in production
                print('Database updated')
            else:
                pass      
        else:
            pass
conn.close()

#Change the timer setting for the required updates frequency. 1 minute by defauls.
def timer():
  threading.Timer(60.0, timer).start()  # Run every 1 minute

  now = datetime.utcnow()
  print(f'Iteration started at:  {now}  UTC')
  new_video_add(
    read_videos(CHANNEL_ID))
    
  check_video_status(TELEGRAM_CHANNEL_ID)

timer() 
    
bot.polling(none_stop=True)



