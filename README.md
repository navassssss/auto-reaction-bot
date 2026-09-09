# Auto Reaction Bot - Complete Documentation

This guide provides step-by-step instructions for hosting, configuring, and using the Telegram Auto Reaction Bot system.

---

## 1. Architecture Overview

This system allows you to manage a fleet of Telegram bots that will automatically react to messages in authorized channels or groups.

*   **Hosting:** Render (Free Web Service)
*   **Database:** Supabase (Free PostgreSQL)
*   **Core Logic:** FastAPI & Asyncio (No Celery/Redis required)
*   **Telegram Library:** `aiogram` 3.x and official Telegram Bot API webhooks.

---

## 2. Setting Up the Admin Bot

The Admin Bot is your control center. You use it to issue commands to the entire system.

1.  Open Telegram and start a chat with [@BotFather](https://t.me/botfather).
2.  Send `/newbot` and follow the prompts to create your admin bot.
3.  Save the **HTTP API Token** provided by BotFather. This will be your `TELEGRAM_BOT_TOKEN`.
4.  Get your own personal Telegram User ID (you can use bots like [@userinfobot](https://t.me/userinfobot) to find your numeric ID, e.g., `123456789`). This will be your `ADMIN_TELEGRAM_IDS`.

---

## 3. Database Hosting (Supabase)

All data, including reaction tasks and authorized channels, must be stored in a persistent database because Render's free tier resets its local files periodically.

1.  Go to [Supabase](https://supabase.com/) and create a free account and a new project.
2.  Go to **Project Settings -> Database** and find your **Connection String (URI)**. It should look like `postgresql://postgres.[YOUR_PROJECT]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`.
3.  Ensure your password is URL-encoded if it contains special characters. This will be your `DATABASE_URL`.
4.  Go to the **SQL Editor** in Supabase and run the exact contents of the `schema.sql` file provided in this repository to create all necessary tables.

---

## 4. Application Hosting (Render)

1.  Push this entire codebase to a private GitHub repository.
2.  Go to [Render](https://render.com/) and click **New -> Web Service**.
3.  Connect your GitHub repository and select it.
4.  Render will automatically use the `render.yaml` configuration file to set up the build and start commands (`pip install -r requirements.txt` and `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
5.  Set the environment variables in the Render dashboard:
    *   `TELEGRAM_BOT_TOKEN`: (Your Admin Bot Token)
    *   `TELEGRAM_WEBHOOK_SECRET`: (A random, secure string you generate, e.g., `my_secret_token_123`)
    *   `ADMIN_TELEGRAM_IDS`: (Your Telegram User ID)
    *   `DATABASE_URL`: (Your Supabase PostgreSQL Connection String)
    *   `WORKER_COUNT`: `2`
    *   `LOG_LEVEL`: `INFO`
6.  Click **Deploy**.

---

## 5. Webhook Configuration

Render does not use "Long Polling" like traditional bots; it uses Webhooks. You need to tell Telegram where to send updates.

Once your Render app is fully deployed and live (e.g., `https://my-reaction-bot.onrender.com`), you must register the webhook:

Open your terminal or use a tool like Postman to make the following request:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_ADMIN_BOT_TOKEN>/setWebhook" \
     -d "url=https://<YOUR_RENDER_APP>.onrender.com/telegram/webhook" \
     -d "secret_token=<YOUR_WEBHOOK_SECRET>"
```
*Replace `<YOUR_ADMIN_BOT_TOKEN>`, `<YOUR_RENDER_APP>`, and `<YOUR_WEBHOOK_SECRET>` with your actual values.*

---

## 6. Configuring Reaction Bots

Reaction bots are the actual bot accounts that will drop the emojis on posts.

1.  Create them via [@BotFather](https://t.me/botfather) just like the Admin Bot.
2.  **CRITICAL:** Telegram requires bots to be **Administrators** in a Channel or have appropriate permissions in a Group to leave reactions. You must add every single Reaction Bot to your target channels as an admin.
3.  Message your Admin Bot with the `/addbot` command:
    ```
    /addbot <YOUR_NEW_BOT_TOKEN> <FRIENDLY_NAME>
    ```
    *Example: `/addbot 123456:ABC-DEF Bot1`*
4.  The system will automatically validate the token with Telegram and store it securely.

*Note: You can view your configured bots in Telegram by messaging the Admin Bot with `/bots`.*

---

## 7. Authorizing Channels

To prevent abuse, the system will only react to posts in explicitly authorized channels.

1.  Find your channel's numeric ID (starts with `-100...`) or its public username (without the `@`).
2.  Message your Admin Bot with the `/addchannel` command:
    ```
    /addchannel <CHAT_ID_OR_USERNAME> <FRIENDLY_TITLE>
    ```
    *Example: `/addchannel -100123456789 My Channel`*

*Note: You can view your authorized channels by messaging the Admin Bot with `/channels`.*

---

## 8. Triggering Reactions

Once a channel is authorized and reaction bots are configured and added to the channel as administrators:

1.  Message your Admin Bot in Telegram.
2.  Send the `/react` command with a URL and an emoji:
    ```
    /react https://t.me/my_cool_channel/123 👍
    ```
3.  The bot will reply with a Job ID and queue the task. 
4.  The background workers inside Render will pick up the task, process the reactions respecting Telegram's rate limits, and update the database.

### Important API Limitations on Reactions:
*   **Custom Emojis:** Standard bots **cannot** use custom premium emojis. Only standard unicode emojis (like 👍, ❤️, 🔥, etc.) are supported by the official API unless you have specific premium bot features unlocked.
*   **Permissions:** If a bot attempts to react but is not an admin or the channel has restricted reactions, the task will fail, and you will see the error via the status command.
*   **Rate Limits:** The system intercepts `429 Too Many Requests` errors from Telegram, automatically pauses the specific worker, and safely requeues the task to comply with Telegram flood limits.

---

## 9. Monitoring and Cancellation

*   **Check Status:** Send `/status JOB-ID` to see how many reactions were successful, failed, or are still pending.
*   **Cancel Job:** Send `/cancel JOB-ID` to stop the pending queue. Note that reactions that have already been placed successfully by the API cannot be easily "undone" in bulk.
