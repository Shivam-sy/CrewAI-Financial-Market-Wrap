import os
import requests
from litellm import completion
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai.llm import LLM
from dotenv import load_dotenv
from datetime import datetime
import time
import logging
from typing import Dict, List, Any
import json


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = "llama-3.1-8b-instant"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

@tool("Tavily Financial News Search")
def tavily_search_tool(query: str) -> str:
    """Search for financial news using Tavily API"""
    if isinstance(query, dict):
        if 'query' in query:
            query = query['query']
        elif 'value' in query:
            query = query['value']
        else:
            query = str(query)
    
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": str(query),  
        "search_depth": "advanced",
        "max_results": 5,
        "include_images": True,
        "include_answer": True
    }
    try:
        logger.info(f"Searching for: {query}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        images = data.get("images", [])

        formatted_results = {
            "news_articles": [
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "published_date": r.get("published_date", "")
                } for r in results[:3]
            ],
            "images": [
                {
                    "url": img.get("url", ""),
                    "description": img.get("description", "")
                } for img in images[:2]
            ]
        }
        return json.dumps(formatted_results, indent=2)

    except Exception as e:
        logger.error(f"Error in Tavily search: {str(e)}")
        return f"Error searching: {str(e)}"

@tool("Financial Chart Finder")
def image_search_tool(search_context: str) -> str:
    """Find relevant financial charts and images based on context"""
    if isinstance(search_context, dict):
        if 'search_context' in search_context:
            search_context = search_context['search_context']
        elif 'value' in search_context:
            search_context = search_context['value']
        else:
            search_context = str(search_context)
    
    query = f"financial charts stock market {search_context} S&P 500 Nasdaq Dow Jones"

    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_images": True
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()

        images = data.get("images", [])
        relevant_images = []

        for img in images[:2]:
            if any(keyword in img.get("description", "").lower()
                   for keyword in ["chart", "graph", "market", "stock", "trading", "financial"]):
                relevant_images.append({
                    "url": img.get("url", ""),
                    "description": img.get("description", ""),
                    "context": "Market visualization"
                })

        return json.dumps(relevant_images, indent=2)

    except Exception as e:
        logger.error(f"Error finding images: {str(e)}")
        return json.dumps([{"url": "", "description": "Chart placeholder", "context": "Error loading image"}])

@tool("Telegram Message Sender")
def telegram_sender_tool(message: str) -> str:
    """Send formatted message to Telegram channel"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        logger.info("Sending message to Telegram...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return "✅ Message sent successfully to Telegram channel"
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")
        return f"❌ Error sending to Telegram: {str(e)}"


def send_to_telegram_direct(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return "Message sent successfully"
    except Exception as e:
        return f"Error sending Telegram message: {str(e)}"

def fetch_market_news():
    """Fetch top US stock market news using Tavily API"""
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": "today US stock market summary, S&P 500, Nasdaq, Dow Jones, major movers",
        "search_depth": "advanced",
        "max_results": 3
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return "No fresh market news found."
        return "\n".join([f"- {r['title']}: {r['url']}" for r in results])
    except Exception as e:
        return f"Error fetching news: {str(e)}"

def generate_market_wrap(news: str) -> str:
    """Generate a concise market wrap using LiteLLM + Groq model."""
    prompt = f"Write a concise (<300 words) US market wrap based on the news:\n{news}"
    retries = 3
    for i in range(retries):
        try:
            response = completion(
                model=f"groq/{GROQ_MODEL_NAME}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,
                timeout=30
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            if "rate limit" in str(e).lower() or "limit" in str(e).lower():
                wait_time = (i + 1) * 15
                logger.info(f"Rate limit reached, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            elif "internal server error" in str(e).lower():
                wait_time = (i + 1) * 10
                logger.info(f"Groq server error, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"LLM Error: {str(e)}")
                return f"Error generating summary: {str(e)}"
    return "Rate limit exceeded or LLM error after retries."


try:
    groq_llm = LLM(
        model=f"groq/{GROQ_MODEL_NAME}",
        temperature=0.7,
        max_tokens=400
    )
    logger.info(f"Successfully initialized Groq LLM with model: {GROQ_MODEL_NAME}")
except Exception as e:
    logger.error(f"LLM initialization error: {str(e)}")
    groq_llm = None

search_agent = Agent(
    role="Financial News Researcher",
    goal="Search and gather the latest US financial market news",
    backstory="You specialize in finding real-time market data and analysis.",
    verbose=True,
    allow_delegation=False,
    tools=[],  
    llm=groq_llm,
    max_iter=1
)

summary_agent = Agent(
    role="Financial Market Analyst",
    goal="Create concise, informative market summaries under 300 words",
    backstory="You are a seasoned financial analyst.",
    verbose=True,
    allow_delegation=False,
    tools=[],
    llm=groq_llm,
    max_iter=1
)

formatting_agent = Agent(
    role="Content & Visual Formatter",
    goal="Format content and find relevant financial charts and images",
    backstory="You know how to present financial info with visuals.",
    verbose=True,
    allow_delegation=False,
    tools=[],  
    llm=groq_llm,
    max_iter=1
)

send_agent = Agent(
    role="Communication Publisher",
    goal="Deliver formatted content to Telegram",
    backstory="You are responsible for sending updates to the channel.",
    verbose=True,
    allow_delegation=False,
    tools=[telegram_sender_tool],
    llm=groq_llm,
    max_iter=1
)

search_task = Task(
    description="Research today's US financial market news and provide a summary of key developments.",
    agent=search_agent,
    expected_output="Summary of key market news and developments",
    human_input=False
)

summary_task = Task(
    description="Create a market summary under 300 words from the research results.",
    agent=summary_agent,
    expected_output="Market summary under 300 words",
    human_input=False
)

formatting_task = Task(
    description="Format the market summary for Telegram with proper Markdown formatting.",
    agent=formatting_agent,
    expected_output="Formatted market wrap ready for Telegram",
    human_input=False
)

send_task = Task(
    description="Send the formatted market summary to Telegram with Markdown.",
    agent=send_agent,
    expected_output="Telegram delivery confirmation",
    human_input=False
)

crew = Crew(
    agents=[search_agent, summary_agent, formatting_agent, send_agent],
    tasks=[search_task, summary_task, formatting_task, send_task],
    process=Process.sequential,
    verbose=True,
    full_output=True,
    output_log_file="crew_execution.log"
)

def validate_environment():
    required_vars = {
        'GROQ_API_KEY': GROQ_API_KEY,
        'TAVILY_API_KEY': TAVILY_API_KEY,
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing = [v for v, val in required_vars.items() if not val]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True

def main():
    logger.info("🚀 Starting CrewAI Financial Market Wrap Workflow...")
    if not validate_environment():
        print("❌ Environment validation failed. Please check your .env file.")
        return

    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

    try:
        logger.info("🤖 Executing CrewAI workflow...")
        start = time.time()
        result = crew.kickoff()
        elapsed = time.time() - start

        logger.info(f"✅ Workflow completed in {elapsed:.2f} seconds")
        print("\n🎉 CREWAI FINANCIAL MARKET WRAP - COMPLETE")
        print("="*80)
        print(result)
        print("="*80)
        return result
    except Exception as e:
        logger.error(f"❌ Workflow failed: {str(e)}")
        print(f"\n🔧 Workflow Error: {str(e)}")
        try:
            logger.info("🔄 Attempting fallback execution...")
            news = fetch_market_news()
            summary = generate_market_wrap(news)
            fallback_message = f"""📊 **US Market Wrap - Fallback ({datetime.now().strftime('%Y-%m-%d')})** 📊

{summary}

🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST
"""
            telegram_result = send_to_telegram_direct(fallback_message)
            logger.info(f"Fallback execution result: {telegram_result}")
            print(f"🔄 Fallback completed: {telegram_result}")
        except Exception as fb_error:
            logger.error(f"❌ Fallback failed: {str(fb_error)}")
            print(f"❌ Complete system failure: {str(fb_error)}")

if __name__ == "__main__":
    main()