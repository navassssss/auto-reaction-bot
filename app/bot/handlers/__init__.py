from app.bot.main import dp
from app.bot.middlewares import AdminAuthMiddleware
import app.bot.handlers.admin

# Register middlewares
dp.message.middleware(AdminAuthMiddleware())
dp.callback_query.middleware(AdminAuthMiddleware())
