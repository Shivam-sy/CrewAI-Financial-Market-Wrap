📌 Project Overview

This project is a CrewAI workflow that generates a daily US financial market wrap after the market closes.
The system retrieves the latest financial news, summarizes it concisely, formats it with charts/images, and sends it automatically to a Telegram channel.

It demonstrates the use of CrewAI agents as independent workers, each focusing on a specific task with guardrails and fallback execution.

⚙️ Setup Instructions
1. Clone the repository
git clone https://github.com/Shivam-sy/CrewAI-Financial-Market-Wrap.git
cd CrewAI-Financial-Market-Wrap

2. Install dependencies
pip install -r requirements.txt

3. Add environment variables

Create a file named .env in the root directory and add your API keys:

GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL_NAME="llama-3.1-8b-instant"
TAVILY_API_KEY="your_tavily_api_key"
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
GEMINI_API_KEY="your_gemini_api_key"


4. Run the script
python main2.py


🤖 Workflow Agents

1. Search Agent → Fetches financial market news using Tavily API

2. Summary Agent → Creates a concise (<500 words) daily summary

3. Formatting Agent → Finds relevant charts/images and integrates them

4. Send Agent → Publishes the summary to Telegram

5. Fallback Mechanism → If Groq API fails, a backup flow fetches and summarizes market news directly

📂 Files in Repository

1. main2.py → Main CrewAI workflow script

2. requirements.txt → Python dependencies

3. crew_execution.log.txt → Logs of workflow execution

4. result.png → Example screenshot of Telegram output

5. README.md → Project documentation

6. .env → Example environment file (replace with your actual keys in .env)

📊 Output Example

Example Telegram message sent by the bot:

📊 **US Market Wrap - Fallback (2025-08-30)** 📊  

**US Market Wrap: August 29, 2025**  

US stock markets experienced a pullback...  
S&P 500 closed 0.8% lower at 4,443, Nasdaq fell 0.9%...  
Despite losses, the index has risen 2.5% in August...  


(See result.png for screenshot proof)

🔧 Features

✅ Modular CrewAI agents (search, summarize, format, send)

✅ API integrations with Tavily, Groq, and Telegram

✅ Error handling + fallback execution when LLM/API fails

✅ Logging for debugging & monitoring

✅ Reusable & extendable pipeline

🚀 Future Improvements

1. Add translation agent (Arabic, Hindi, Hebrew)

2. Auto-insert charts/graphs in Telegram messages

3. Integrate YouTube/X feeds for richer context


4. Support multi-language daily reports
