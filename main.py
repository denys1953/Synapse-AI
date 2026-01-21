import chromadb
import os

# Автоматичне визначення хоста: 
# Якщо код у Docker — використовуємо "chroma", якщо на Mac — "localhost"
host = "chroma" if os.getenv("DOCKER_MODE") else "localhost"

try:
    chroma_client = chromadb.HttpClient(
        host=host,
        port=8000
    )

    chroma_client.delete_collection(name="notebook_3")

    collections = chroma_client.list_collections()
    
    print(f"--- Connected to ChromaDB at {host} ---")
    if not collections:
        print("No collections found.")
    else:
        print(f"Found {len(collections)} collections:")
        for col in collections:
            # col — це об'єкт Collection, виводимо його ім'я
            print(f" - {col.name}")

    collection = chroma_client.get_collection(name="notebook_1")

    print(f"Total items in 'notebook_1': {collection.count()}")

    # 2. Get the first 5 items (Preview)
    # .peek() is a helper to see a few items with their data
    peek_results = collection.peek(limit=5)

    print("\n--- Preview (First 5 items) ---")
    for i in range(len(peek_results['ids'])):
        print(f"\nID: {peek_results['ids'][i]}")
        print(f"Metadata: {peek_results['metadatas'][i]}")
        # Truncate text for readability
        content = peek_results['documents'][i][:100] + "..." 
        print(f"Content: {content}")
except Exception as e:
    print(f"FAILED to connect: {e}")
    print("\n💡 TIP: If running on Mac, ensure ports are mapped in docker-compose.yml")