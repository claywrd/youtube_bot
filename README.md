# youtube_bot

### The bot is used to collect statistics of the latest videos

Before starting, modify the .env.example -> .env file and provide the required parameters.

On the first start, the bot will create an SQLite database and will try to populate it with 10 latest videos from the channel.

#### IMPORTANT: Please expect many requests and update messages during the first iterations.

After the database population, the bot will be checking for a new video once a minute.
New videos will be placed into the database which plays a role of the waiting queue as well as of the statistics storage.

An hour after a video is published, the bot will collect numbers of Views, Likes, and Comments, update the database accordingly, and send a report to the specified TG channel.

Check intervals may be changed in the “timer” function.

Please also see the comments in the code.
