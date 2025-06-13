import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TDSDiscourseScraper:
    def __init__(self, base_url="https://discourse.onlinedegree.iitm.ac.in", 
                 category_id=34, date_from=None, date_to=None):
        self.BASE_URL = base_url
        self.CATEGORY_ID = category_id
        self.CATEGORY_JSON_URL = f"{base_url}/c/courses/tds-kb/{category_id}.json"
        self.AUTH_STATE_FILE = "data/raw/auth.json"
        self.OUTPUT_FILE = "data/raw/discourse_posts.json"
        
        # Set default date range if not provided
        self.DATE_FROM = date_from or datetime(2025, 1, 1)
        self.DATE_TO = date_to or datetime(2025, 4, 14)
        
        # Ensure data directories exist
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)

    def parse_date(self, date_str):
        """Parse date string from Discourse API"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    def login_and_save_auth(self, playwright):
        """Handle manual login and save authentication state"""
        logger.info("🔐 No auth found. Launching browser for manual login...")
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(f"{self.BASE_URL}/login")
            logger.info("🌐 Please log in manually using Google. Then press ▶️ (Resume) in Playwright bar.")
            page.pause()
            context.storage_state(path=self.AUTH_STATE_FILE)
            logger.info("✅ Login state saved.")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
        finally:
            browser.close()

    def is_authenticated(self, page):
        """Check if current session is authenticated"""
        try:
            page.goto(self.CATEGORY_JSON_URL, timeout=10000)
            page.wait_for_selector("pre", timeout=5000)
            json.loads(page.inner_text("pre"))
            return True
        except (TimeoutError, json.JSONDecodeError):
            return False

    def scrape_posts(self, playwright):
        """Main scraping function"""
        logger.info("🔍 Starting scrape using saved session...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(storage_state=self.AUTH_STATE_FILE)
        page = context.new_page()

        try:
            all_topics = self._fetch_all_topics(page)
            filtered_posts = self._process_topics(page, all_topics)
            self._save_posts(filtered_posts)
            
            logger.info(f"✅ Scraped {len(filtered_posts)} posts between {self.DATE_FROM.date()} and {self.DATE_TO.date()}")
            return filtered_posts
        
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            browser.close()

    def _fetch_all_topics(self, page):
        """Fetch all topics from paginated API"""
        all_topics = []
        page_num = 0
        
        while True:
            paginated_url = f"{self.CATEGORY_JSON_URL}?page={page_num}"
            logger.info(f"📦 Fetching page {page_num}...")
            page.goto(paginated_url)

            try:
                # Try to get JSON from pre tag first, then from page content
                try:
                    data = json.loads(page.inner_text("pre"))
                except:
                    data = json.loads(page.content())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON for page {page_num}")
                break

            topics = data.get("topic_list", {}).get("topics", [])
            if not topics:
                break

            all_topics.extend(topics)
            page_num += 1

        logger.info(f"📄 Found {len(all_topics)} total topics across all pages")
        return all_topics

    def _process_topics(self, page, all_topics):
        """Process topics and extract posts within date range"""
        filtered_posts = []
        
        for i, topic in enumerate(all_topics):
            if i % 10 == 0:
                logger.info(f"Processing topic {i+1}/{len(all_topics)}")
                
            created_at = self.parse_date(topic["created_at"])
            if not (self.DATE_FROM <= created_at <= self.DATE_TO):
                continue

            topic_url = f"{self.BASE_URL}/t/{topic['slug']}/{topic['id']}.json"
            page.goto(topic_url)
            
            try:
                try:
                    topic_data = json.loads(page.inner_text("pre"))
                except:
                    topic_data = json.loads(page.content())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse topic data for {topic['id']}")
                continue

            posts = topic_data.get("post_stream", {}).get("posts", [])
            accepted_answer_id = topic_data.get("accepted_answer", 
                                               topic_data.get("accepted_answer_post_id"))

            # Build reply count map
            reply_counter = {}
            for post in posts:
                reply_to = post.get("reply_to_post_number")
                if reply_to is not None:
                    reply_counter[reply_to] = reply_counter.get(reply_to, 0) + 1

            # Process each post
            for post in posts:
                filtered_posts.append({
                    "topic_id": topic["id"],
                    "topic_title": topic.get("title"),
                    "category_id": topic.get("category_id"),
                    "tags": topic.get("tags", []),
                    "post_id": post["id"],
                    "post_number": post["post_number"],
                    "author": post["username"],
                    "created_at": post["created_at"],
                    "updated_at": post.get("updated_at"),
                    "reply_to_post_number": post.get("reply_to_post_number"),
                    "is_reply": post.get("reply_to_post_number") is not None,
                    "reply_count": reply_counter.get(post["post_number"], 0),
                    "like_count": post.get("like_count", 0),
                    "is_accepted_answer": post["id"] == accepted_answer_id,
                    "mentioned_users": [u["username"] for u in post.get("mentioned_users", [])],
                    "url": f"{self.BASE_URL}/t/{topic['slug']}/{topic['id']}/{post['post_number']}",
                    "content": BeautifulSoup(post["cooked"], "html.parser").get_text()
                })

        return filtered_posts

    def _save_posts(self, posts):
        """Save posts to JSON file"""
        with open(self.OUTPUT_FILE, "w", encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved posts to {self.OUTPUT_FILE}")

    def run(self):
        """Main execution function"""
        with sync_playwright() as p:
            # Handle authentication
            if not os.path.exists(self.AUTH_STATE_FILE):
                self.login_and_save_auth(p)
            else:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(storage_state=self.AUTH_STATE_FILE)
                page = context.new_page()
                
                if not self.is_authenticated(page):
                    logger.info("⚠️ Session invalid. Re-authenticating...")
                    browser.close()
                    self.login_and_save_auth(p)
                else:
                    logger.info("✅ Using existing authenticated session.")
                    browser.close()

            # Scrape posts
            return self.scrape_posts(p)

def main():
    """Main function for standalone execution"""
    scraper = TDSDiscourseScraper()
    posts = scraper.run()
    print(f"Successfully scraped {len(posts)} posts!")

if __name__ == "__main__":
    main()