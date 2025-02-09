import asyncio
import pytest
from src.async_modules.information_extractor import InformationExtractor
import sqlite3

@pytest.mark.asyncio
async def test_extractor():
    # Create sample chat history
    chat_history = [
        {"role": "user", "content": "I'm really interested in learning about Japanese tea ceremonies."},
        {"role": "assistant", "content": "That's wonderful! The Japanese tea ceremony, or chanoyu, is a beautiful cultural practice. Would you like to learn about its history or the specific steps involved?"},
        {"role": "user", "content": "Yes, please tell me about the history. Also, could you recommend some places where I could experience a tea ceremony?"},
        {"role": "assistant", "content": "The Japanese tea ceremony dates back to the 9th century. As for experiencing it, many traditional tea houses in Kyoto offer ceremonies for visitors. Would you like me to suggest some specific locations?"},
        {"role": "user", "content": "Yes, that would be great! I'm planning to visit Kyoto next spring."}
    ]
    
    # Create extractor and process chat history
    extractor = InformationExtractor()
    result = await extractor.process(chat_history)
    
    # Print results
    print("\nExtracted Information:")
    for category, items in result.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for item in items:
            print(f"- {item}")
    
    # Print stored information from database
    print("\nStored Information from Database:")
    with sqlite3.connect('data/chat.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, category, item 
            FROM extracted_information 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        for timestamp, category, item in cursor.fetchall():
            print(f"{timestamp} - {category}: {item}")

if __name__ == "__main__":
    asyncio.run(test_extractor()) 