import yaml
from src.connectors.notion import NotionConnector

# Load config
with open('config/credentials.yaml') as f:
    config = yaml.safe_load(f)

api_key = config['notion']['api_key']

connector = NotionConnector(api_key=api_key)
print("✅ Connected to Notion")

print("\n" + "="*60)
print("NOTION SETUP INSTRUCTIONS")
print("="*60)
print("\n1. Go to https://notion.so")
print("2. Create a new page (e.g., 'Newsletter Analysis')")
print("3. Share it with your integration:")
print("   - Click '...' → 'Add connections' → Select your integration")
print("4. Copy the page ID from the URL")
print("   URL format: https://www.notion.so/Page-Name-XXXXX")
print("   The page ID is the XXXXX part (32 characters)")
print("\n" + "="*60)

page_id = input("\nPaste the page ID here: ").strip()

# Remove any dashes if user copied with them
page_id = page_id.replace('-', '')

print(f"\nCreating databases in page {page_id}...")

try:
    newsletter_db = connector.create_newsletter_database(parent_page_id=page_id)
    print(f"✅ Newsletter DB: {newsletter_db}")
    
    stories_db = connector.create_stories_database(parent_page_id=page_id)
    print(f"✅ Stories DB: {stories_db}")
    
    # Update config
    config['notion']['databases']['newsletters'] = newsletter_db
    config['notion']['databases']['stories'] = stories_db
    
    with open('config/credentials.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("\n✅ Setup complete!")
    print(f"\nNewsletter DB: {newsletter_db}")
    print(f"Stories DB: {stories_db}")
    print("\nDatabases saved to config/credentials.yaml")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure:")
    print("1. The page ID is correct")
    print("2. You shared the page with your integration")
