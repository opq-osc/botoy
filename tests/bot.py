import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent.parent))


from botoy import AsyncBotoy, S
from botoy.async_decorators import equal_content

bot = AsyncBotoy(use_plugins=True)


@bot.on_group_msg
@equal_content("test")
async def help(_):
    await S.atext(bot.plugMgr.help)


if __name__ == "__main__":
    asyncio.run(bot.run())
