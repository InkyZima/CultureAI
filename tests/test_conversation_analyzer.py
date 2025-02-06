import asyncio
from src.async_modules.conversation_analyzer import ConversationAnalyzer
from src.async_modules.information_extractor import InformationExtractor
import sqlite3

async def test_analyzer():
    # Create sample chat history
    chat_history = [
        {"role": "user", "content": "I'm really interested in learning about Japanese tea ceremonies."},
        {"role": "assistant", "content": "That's wonderful! The Japanese tea ceremony, or chanoyu, is a beautiful cultural practice. Would you like to learn about its history or the specific steps involved?"},
        {"role": "user", "content": "Yes, please tell me about the history. Also, could you recommend some places where I could experience a tea ceremony?"},
        {"role": "assistant", "content": "The Japanese tea ceremony dates back to the 9th century. As for experiencing it, many traditional tea houses in Kyoto offer ceremonies for visitors. Would you like me to suggest some specific locations?"},
        {"role": "user", "content": "Yes, that would be great! I'm planning to visit Kyoto next spring."}
    ]
    
    # First get extracted information
    extractor = InformationExtractor()
    extracted_info = await extractor.process(chat_history)
    
    # Create analyzer and process chat history with extracted info
    analyzer = ConversationAnalyzer()
    result = await analyzer.process(chat_history, extracted_info)
    
    # Print analysis results
    print("\nConversation Analysis Results:")
    print(f"\nEngagement Level: {result['engagement_level']}")
    
    for category in ['cultural_learning', 'guidance_needed', 'suggested_topics']:
        print(f"\n{category.replace('_', ' ').title()}:")
        for item in result[category]:
            print(f"- {item}")
    
    # Print stored analysis from database
    print("\nStored Analysis from Database:")
    with sqlite3.connect('data/chat.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                timestamp,
                engagement_level,
                cultural_learning,
                guidance_needed,
                suggested_topics
            FROM conversation_analysis 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            timestamp, engagement, learning, guidance, topics = row
            print(f"\nTimestamp: {timestamp}")
            print(f"Engagement Level: {engagement}")
            print("\nCultural Learning:")
            for item in learning.split('\n'):
                if item.strip():
                    print(f"- {item}")
            print("\nGuidance Needed:")
            for item in guidance.split('\n'):
                if item.strip():
                    print(f"- {item}")
            print("\nSuggested Topics:")
            for item in topics.split('\n'):
                if item.strip():
                    print(f"- {item}")

if __name__ == "__main__":
    asyncio.run(test_analyzer())
