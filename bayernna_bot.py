import asyncio
import logging
import re
import feedparser
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode
from deep_translator import GoogleTranslator

BOT_TOKEN = "8649215051:AAFxxZeDwIfIE79JwAzpB_7P2SiL6qem-Xk"
CHANNEL_ID = "@Bayernna"

RSS_FEEDS = [
    ("https://www.skysports.com/rss/12040", "Sky Sports"),
    ("https://www.goal.com/en/feeds/news?fmt=rss", "Goal"),
    ("https://feeds.bbci.co.uk/sport/football/rss.xml", "BBC Sport"),
]

KEYWORDS = ["bayern", "munich", "بايرن", "ميونخ", "FCB"]

posted_news = set()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def clean_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def is_bayern_news(title, summary):
    text = (title + " " + summary).lower()
    return any(k.lower() in text for k in KEYWORDS)

def translate_to_arabic(text):
    try:
        if not text:
            return ""
        if len(text) > 4500:
            text = text[:4500]
        translator = GoogleTranslator(source='auto', target='ar')
        return translator.translate(text) or text
    except Exception as e:
        logger.warning(f"فشل الترجمة: {e}")
        return text

def format_message(title_ar, summary_ar, link, source):
    summary_text = f"\n\n📝 {summary_ar[:250]}..." if summary_ar else ""
    return (
        f"🔴⚪ *أخبار البايرن*\n\n"
        f"📌 *{title_ar}*"
        f"{summary_text}\n\n"
        f"🔗 [اقرأ الخبر كاملاً]({link})\n\n"
        f"📡 {source}\n"
        f"🕐 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n\n"
        f"#بايرننا #البايرن #Bayern #FCBayern"
    )

async def fetch_and_post(bot):
    logger.info("🔍 جاري البحث عن أخبار جديدة...")
    new_posts = 0
    for feed_url, source_name in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                entry_id = entry.get("id") or entry.get("link", "")
                if entry_id in posted_news:
                    continue
                title = clean_html(entry.get("title", ""))
                summary = clean_html(entry.get("summary", ""))
                link = entry.get("link", "")

                if not is_bayern_news(title, summary):
                    continue

                title_ar = translate_to_arabic(title)
                summary_ar = translate_to_arabic(summary[:500]) if summary else ""
                message = format_message(title_ar, summary_ar, link, source_name)

                await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
                posted_news.add(entry_id)
                new_posts += 1
                logger.info(f"✅ تم نشر: {title_ar}")
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    logger.info(f"📬 تم نشر {new_posts} خبر" if new_posts else "📭 لا توجد أخبار بايرن جديدة")

async def send_morning_message(bot):
    message = "🌅 *صباح الخير من بايرننا!*\n\n🔴 تابعوا معنا أخبار البايرن\n\n_Mia San Mia_ 🇩🇪\n\n#بايرننا #البايرن"
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)

async def main():
    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    logger.info(f"🤖 البوت يعمل: @{me.username}")
    scheduler = AsyncIOScheduler(timezone="Asia/Amman")
    scheduler.add_job(fetch_and_post, "interval", hours=1, args=[bot])
    scheduler.add_job(send_morning_message, "cron", hour=9, minute=0, args=[bot])
    scheduler.start()
    logger.info("⏰ جاهز للنشر!")
    await fetch_and_post(bot)
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
