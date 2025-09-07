from agents.base_agent import BaseAgent

def test_connection():
    agent = BaseAgent()
    if agent.model:
        print("Connection successful!")
        # Test with a simple prompt
        response = agent.model.generate_content("What is market analysis?")
        print(f"\nTest response: {response.text}")

if __name__ == "__main__":
    test_connection()