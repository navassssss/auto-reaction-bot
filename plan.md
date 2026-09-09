Build a production-quality Telegram reaction-management application using Python, Render, Supabase, and the official Telegram Bot API.

IMPORTANT SCOPE:
The system is only for Telegram bots/accounts that the operator legitimately controls and Telegram channels/groups where the operator has authorization.

Do not implement:

* fake-account creation
* unauthorized Telegram accounts
* anti-spam bypasses
* flood-limit circumvention
* proxy rotation intended to evade Telegram restrictions
* techniques intended to manipulate or evade Telegram's platform protections

Use only the official Telegram Bot API.

# 1. FREE INFRASTRUCTURE

The target deployment is:

* Render Free Web Service
* Supabase Free project
* GitHub
* Telegram Bot API

Do not require:

* VPS
* paid server
* paid database
* Redis
* Celery
* RabbitMQ
* Kubernetes
* paid monitoring
* paid API services

All persistent application data must be stored in Supabase PostgreSQL.

Do NOT use SQLite for production because Render's free filesystem is ephemeral.

# 2. ARCHITECTURE

Use this architecture:

Telegram
|
v
Telegram Webhook
|
v
Render Free Web Service
|
+--------------------+
|                    |
v                    v
Admin Bot Logic       Supabase
|                 PostgreSQL
|
v
Reaction Job Manager
|
v
Async Worker Tasks
|
v
Official Telegram Bot API

Use FastAPI as the HTTP server.

The application must expose:

POST /telegram/webhook

for Telegram updates.

Also expose:

GET /health

which returns a simple health response.

# 3. TECHNOLOGY

Use:

* Python 3.12+
* FastAPI
* aiogram 3.x
* SQLAlchemy 2.x
* asyncpg
* PostgreSQL
* Pydantic Settings
* Alembic
* httpx
* pytest

Keep dependencies minimal.

Do not add Redis unless absolutely required.

For the initial implementation, use asyncio-based task processing inside the Render service.

# 4. TELEGRAM ADMIN BOT

Create an admin bot.

Supported commands:

/start
/help
/react
/status
/cancel
/bots
/channels

Only Telegram user IDs configured in:

ADMIN_TELEGRAM_IDS

can use administrative functions.

Unauthorized users must receive:

"Access denied."

Do not reveal whether an account exists or provide internal information.

# 5. /react

Support:

/react <telegram_post_link> <emoji>

Example:

/react https://t.me/my_channel/123 👍

Parse:

* Telegram channel/group
* message ID
* emoji

Validate all fields.

Only allow reactions against destinations stored in the authorized_channels table.

After creating a job:

Reaction job created.

Job ID: JOB-12345
Post: @my_channel/123
Reaction: 👍
Bots: 10
Status: queued

# 6. CHANNEL AUTHORIZATION

Create:

authorized_channels

Fields:

id
telegram_chat_id
username
title
enabled
created_at
updated_at

The administrator must explicitly authorize destinations before they can be used.

Implement:

/channels

and an inline-button interface for:

* Add channel
* Enable channel
* Disable channel
* Remove channel
* List channels

Never allow arbitrary channels simply because a user submitted a URL.

# 7. BOT REGISTRY

Create:

reaction_bots

Fields:

id
name
telegram_bot_id
token_encrypted
enabled
created_at
updated_at
last_success_at
last_error_at

Never expose tokens through Telegram or logs.

Use environment variables or secure encryption.

For the first implementation, support adding bot credentials through an admin-only flow.

When registering a bot:

1. Validate its token against Telegram.
2. Get the bot's Telegram ID.
3. Store the bot.
4. Never display the token again.

# 8. DATABASE

Use Supabase PostgreSQL.

Tables:

admins
authorized_channels
reaction_bots
reaction_jobs
reaction_tasks
audit_logs

## reaction_jobs

Fields:

id
job_id
telegram_chat_id
message_id
post_url
emoji
status
total_tasks
successful_tasks
failed_tasks
pending_tasks
created_at
started_at
completed_at

Statuses:

queued
running
completed
partially_completed
failed
cancelled

## reaction_tasks

Fields:

id
job_id
bot_id
status
attempts
error_code
error_message
created_at
started_at
completed_at

Statuses:

pending
running
success
failed
cancelled

Add appropriate PostgreSQL indexes.

# 9. JOB PROCESSING

When /react is received:

1. Authenticate administrator.
2. Parse URL.
3. Validate authorized channel.
4. Validate message.
5. Validate reaction.
6. Load enabled reaction bots.
7. Create reaction_job.
8. Create reaction_task records.
9. Return job ID.
10. Process tasks asynchronously.
11. Update database.
12. Send final result to the administrator.

The database must be the source of truth.

Do not rely on in-memory state for job persistence.

# 10. ASYNC WORKERS

Do not introduce Redis initially.

Use asyncio workers inside the Render service.

Create a configurable worker pool:

WORKER_COUNT=2

Workers should:

1. Claim pending tasks.
2. Mark them running.
3. Execute Telegram API operation.
4. Record success/failure.
5. Continue with the next task.

Use PostgreSQL transactions/locking to avoid two workers processing the same task.

Design the worker layer so Redis/Celery could be added later if necessary.

# 11. RATE LIMITING

Respect Telegram's documented API limits.

Implement conservative rate limiting.

If Telegram responds with a retry-after/flood-wait error:

* record the error
* wait for the specified duration when appropriate
* retry according to policy
* do NOT attempt to circumvent the restriction

Never use bot rotation, proxies, or other techniques to bypass Telegram's restrictions.

# 12. TELEGRAM REACTION API

Create:

TelegramReactionService

with methods such as:

validate_bot()
validate_chat()
set_reaction()

Before implementing the actual request, check the CURRENT official Telegram Bot API documentation and verify:

* exact method name
* request parameters
* supported emoji/custom emoji
* bot permissions
* channel restrictions
* group restrictions

Do not assume that every Telegram bot can react to every message.

Use only documented Telegram Bot API functionality.

# 13. WEBHOOK

Use Telegram webhook mode rather than long polling.

Environment variables:

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

The webhook URL should be:

https://<render-service>.onrender.com/telegram/webhook

Validate the Telegram webhook secret.

Provide a setup function that registers the webhook automatically on application startup.

Also provide an admin/setup command or script to remove and reset the webhook.

# 14. RENDER

The project must deploy as a Render Web Service.

Create:

render.yaml

or provide exact Render configuration.

The service should:

* run FastAPI
* listen on Render's PORT environment variable
* expose /health
* expose /telegram/webhook
* connect to Supabase
* use HTTPS automatically through Render

Example start command:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Do not hardcode the port.

# 15. SUPABASE

Use Supabase PostgreSQL as the persistent database.

Provide:

* schema.sql
* Alembic migrations where appropriate
* database connection configuration
* connection pooling configuration

Environment variable:

DATABASE_URL=

Do not commit credentials.

The application must work with Supabase's free PostgreSQL tier.

# 16. ENVIRONMENT VARIABLES

Create .env.example:

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
ADMIN_TELEGRAM_IDS=
DATABASE_URL=
WORKER_COUNT=2
LOG_LEVEL=INFO

Never include real credentials.

Create .gitignore entries for:

.env
.env.*
!.env.example

# 17. /status

Implement:

/status JOB-12345

Return:

Job: JOB-12345
Status: running

Post: @my_channel/123
Reaction: 👍

Total: 10
Successful: 6
Failed: 1
Pending: 3

Use the database for these values.

# 18. /cancel

Implement:

/cancel JOB-12345

Pending tasks should become cancelled.

Already completed Telegram API operations cannot necessarily be undone.

Report this correctly.

# 19. /bots

Implement:

/bots

Display:

Reaction bots

Enabled: 8
Disabled: 2

For individual bots show:

Name
Status
Last success
Last error

Never show bot tokens.

Provide inline buttons for:

Enable
Disable
Delete

# 20. AUDIT LOG

Create:

audit_logs

Fields:

id
admin_telegram_id
action
job_id
target_chat_id
target_message_id
created_at
metadata

Log:

* job creation
* job cancellation
* bot creation
* bot enable/disable
* channel authorization
* channel removal

Do not store unnecessary personal data.

# 21. SECURITY

Implement:

* admin allowlist
* webhook secret validation
* input validation
* SQL parameterization
* token protection
* safe logging
* database transactions
* authorization checks
* rate limiting
* error sanitization

Never expose stack traces through Telegram.

Never log:

* bot tokens
* database passwords
* webhook secrets
* authorization headers

# 22. RENDER FREE-TIER CONSIDERATIONS

Design the application to tolerate Render free-service restarts and spin-downs.

Do not rely on:

* local files
* local SQLite
* in-memory job state
* local queues as the only source of truth

All important state must be persisted in Supabase.

On application startup:

1. Connect to Supabase.
2. Find jobs/tasks left in "running".
3. Safely recover them.
4. Requeue appropriate unfinished tasks.
5. Start workers.
6. Register/verify Telegram webhook.
7. Start FastAPI.

Make recovery idempotent.

# 23. HEALTH CHECK

Implement:

GET /health

Return JSON similar to:

{
"status": "ok",
"database": "ok",
"service": "telegram-reaction-manager"
}

Do not expose secrets or database credentials.

# 24. TESTING

Use pytest.

Test:

* admin authorization
* webhook authentication
* post URL parsing
* authorized channel validation
* bot registration
* job creation
* task creation
* task claiming
* task idempotency
* cancellation
* restart recovery
* Telegram API errors
* retry-after handling
* database failures
* token redaction

Mock Telegram API calls.

Never send real reactions during tests.

# 25. GITHUB

Prepare the project for GitHub.

Include:

README.md
.env.example
.gitignore
requirements.txt or pyproject.toml
render.yaml
schema.sql
alembic/
app/
tests/

Do not commit:

.env
credentials
Telegram tokens
Supabase service keys

# 26. README

Write complete setup instructions.

Include:

## Step 1

Create Telegram admin bot.

## Step 2

Create the Supabase project.

## Step 3

Create the PostgreSQL schema.

## Step 4

Create the Render Web Service.

## Step 5

Connect the GitHub repository.

## Step 6

Configure Render environment variables.

## Step 7

Deploy.

## Step 8

Configure Telegram webhook.

## Step 9

Register authorized reaction bots.

## Step 10

Authorize Telegram channels.

## Step 11

Test:

/react https://t.me/example/123 👍

## Step 12

Check:

/status JOB-ID

# 27. COST REQUIREMENT

The intended initial configuration is:

Render:
Free Web Service

Supabase:
Free Project

GitHub:
Free repository

Telegram:
Official Bot API

No paid third-party services.

Clearly document the limitations of free tiers rather than pretending they provide production-grade uptime.

# 28. IMPORTANT IMPLEMENTATION DETAIL

Do NOT blindly implement the Telegram reaction endpoint from memory.

Before writing the TelegramReactionService, inspect the latest official Telegram Bot API documentation and verify that the desired bot reaction functionality is currently available for the exact target chat/message type.

If the Bot API does not permit the requested operation, do not replace it with unofficial user-account automation.

Instead, clearly report the limitation.

# 29. FINAL ACCEPTANCE TEST

The application is complete when:

1. Render successfully deploys it.
2. /health works.
3. Telegram webhook reaches Render.
4. Unauthorized Telegram users are rejected.
5. Authorized admins can submit an authorized post link.
6. A job is persisted in Supabase.
7. Reaction tasks are persisted.
8. Workers process tasks.
9. Results are persisted.
10. /status reports accurate progress.
11. /cancel works.
12. Render restarts do not destroy job data.
13. Supabase contains all persistent state.
14. No secrets appear in GitHub or logs.
15. Tests pass.
16. No unofficial Telegram APIs or anti-limit mechanisms are used.

After completing the implementation, provide:

* complete file tree
* setup instructions
* Supabase SQL
* Render configuration
* environment variables
* deployment commands
* test commands
* explanation of the Telegram reaction API limitations
