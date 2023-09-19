# youtube_bot

### The bot is used to collect statistics of the latest videos

Before starting, edit the .env.example file and provide the required parameters.

On the first start, the bot will create an SQLite database and will try to populate it with the 50 latest videos on the channel.

#### IMPORTANT: Please expect a lot of requests and update messages during the first iterations.

After the database population, the bot will check for a new video once a minute.
New videos will be placed into the database which plays a role of a waiting queue as well as of the statistics storage.

An hour after the video is published, the bot will collect the number of Views, Likes, and Comments and update the database accordingly.

Check intervals may be changed in the “timer” function.

Please also see the comments in the code.
