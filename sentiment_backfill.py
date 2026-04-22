import os
import env_loader
import anthropic
import re
import time
from db_utils import get_db_connection

def get_claude_analysis(headline, ticker):
    """Scores RNS and provides a brief rationale with robust parsing."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_id = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""
        Analyze this AIM stock headline for {ticker}: "{headline}"
        Output strictly in this format: [SCORE] | [RATIONALE]
        Example: 0.5 | Strong revenue growth exceeding expectations.
        """
        
        message = client.messages.create(
            model=model_id,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        res = message.content[0].text.strip()
        
        if "|" in res:
            score_part, rationale = res.split("|", 1)
            clean_score_str = score_part.replace("SCORE", "").replace("Score", "").replace(":", "").strip()
            match = re.search(r"[-+]?\d*\.\d+|\d+", clean_score_str)
            if match:
                return float(match.group()), rationale.strip()
        
        return 0.0, res # Fallback
            
    except Exception as e:
        print(f"    ⚠️ AI Error: {e}")
        return None, None

def run_backfill():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # 1. Find records where rationale is NULL or empty
    # We join with companies to get the ticker for better AI context
    query = """
        SELECT ra.rns_id, ra.headline, c.ticker 
        FROM rns_announcements ra
        JOIN companies c ON ra.company_id = c.company_id
        WHERE ra.sentiment_rationale IS NULL OR ra.sentiment_rationale = ''
        ORDER BY ra.timestamp DESC
    """
    
    cursor.execute(query)
    records = cursor.fetchall()
    
    print(f"🔄 Found {len(records)} records requiring analysis.")

    for i, row in enumerate(records):
        print(f"[{i+1}/{len(records)}] Processing {row['ticker']}: {row['headline'][:50]}...")
        
        score, rationale = get_claude_analysis(row['headline'], row['ticker'])
        
        if score is not None:
            update_sql = """
                UPDATE rns_announcements 
                SET sentiment_score = %s, sentiment_rationale = %s 
                WHERE rns_id = %s
            """
            cursor.execute(update_sql, (score, rationale, row['rns_id']))
            conn.commit()
            print(f"    ✅ Updated: {score}")
            
            # 2. Add a tiny sleep to be kind to the API rate limits
            time.sleep(1)
        else:
            print(f"    ❌ Skipped due to AI error.")

    cursor.close()
    conn.close()
    print("\n🏁 Backfill Complete.")

if __name__ == "__main__":
    run_backfill()