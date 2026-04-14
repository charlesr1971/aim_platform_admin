import os
import env_loader
import anthropic
from pathlib import Path


def list_allowed_models():
    print("--- Querying Available Anthropic Models ---")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ Error: No API Key found in .env")
        return

    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Fetch the list of models from the API
        models = client.models.list()
        
        print(f"✅ Successfully retrieved {len(models.data)} models:\n")
        for model in models.data:
            print(f"ID: {model.id}")
            print(f"Name: {model.display_name}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ API Error: {str(e)}")

if __name__ == "__main__":
    list_allowed_models()
