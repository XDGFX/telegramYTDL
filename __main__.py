import os
import re
import time

import youtube_dl
from dotenv import load_dotenv
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import CallbackContext, MessageHandler, Updater
from telegram.ext.filters import Filters

load_dotenv()

updater = Updater(token=os.getenv("TELEGRAM_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")


def format_progress(data):
    """
    Automatically format a ytdl progress report into nice to read text
    """
    if data["status"] == "downloading":
        return f"Downloading: {data['_percent_str']} complete"
    elif data["status"] == "finished":
        return f"Download complete"
    elif data["status"] == "error":
        return f"Error: {data['error']}"
    else:
        return f"Unknown status: {data['status']}"


def msg(update: Update, context: CallbackContext):
    class DownloadProgress:
        def __init__(self):
            # Send a progress message to the user, this will be updated with
            # each progress update
            self.message_id = context.bot.send_message(
                chat_id=update.effective_chat.id, text="Downloading...", timeout=10
            ).message_id

            self.previous_update_message = None
            self.last_update_time = None

        def update(self, data):

            # Only update the message if it's been more than a second since
            # the last update
            if self.last_update_time is None or time.time() - self.last_update_time > 1:

                # Format the progress report
                progress_report = format_progress(data)

                # If the previous update message is the same as the current one,
                # don't send another one
                if self.previous_update_message == progress_report:
                    return

                # Update the previous update message
                self.previous_update_message = progress_report

                # Update the progress message
                try:
                    context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=self.message_id,
                        text=progress_report,
                    )
                except TimedOut:
                    pass

    dp = DownloadProgress()

    # YouTube-dl options
    ydl_opts = {
        "progress_hooks": [dp.update],
        "nooverwrites": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s-%(id)s.%(ext)s",
    }

    # Confirm reciept of message
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Message recieved, sending to downloader"
    )

    # Validate that the message is a website url
    if not re.match(
        r"((http|https)://)(www.)?[a-zA-Z0-9@:%._+~#?&//=]{2,256}.[a-z]{2,6}\b([-a-zA-Z0-9@:%._+~#?&//=]*)",
        update.message.text,
    ):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid URL")

        # Delete the message
        context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id
        )
        return

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([update.message.text])

    # Delete the message received
    context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=update.message.message_id
    )


msg_handler = MessageHandler(Filters.all, msg)
dispatcher.add_handler(msg_handler)

updater.start_polling()

print("Bot started")

updater.idle()
