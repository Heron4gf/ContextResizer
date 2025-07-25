import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_comprehensive():
    """Comprehensive test for OpenAI client compatibility."""
    
    print("🧪 Comprehensive OpenAI Client Compatibility Test")
    print("=" * 60)
    
    # Test data
    test_data = {
        "model": "gpt-4.1-nano",
        "messages": [{"role": "user", "content": "Hello from ContextResizer!"}],
        "max_tokens": 50
    }
    
    tests = [
        {
            "name": "Basic OpenAI Client Format",
            "url": "http://localhost:8000/v1/openai/chat/completions",
            "data": test_data,
            "expected": 200
        },
        {
            "name": "Health Check",
            "url": "http://localhost:8000/health",
            "method": "GET",
            "expected": 200
        },
        {
            "name": "Context Resizing Endpoint",
            "url": "http://localhost:8000/v1/auto-resize",
            "data": {
                "context": '{"role": "user", "content": "Hello"}\n{"role": "assistant", "content": "Hi there!"}',
                "max_tokens": 100
            },
            "expected": 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n📋 Testing: {test['name']}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                method = test.get('method', 'POST')
                
                if method == 'GET':
                    response = await client.get(test['url'])
                else:
                    response = await client.post(
                        test['url'],
                        json=test['data'],
                        headers={"Content-Type": "application/json"}
                    )
                
                if response.status_code == test['expected']:
                    print(f"   ✅ PASS - Status: {response.status_code}")
                    if test['name'] == "Basic OpenAI Client Format":
                        try:
                            data = response.json()
                            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            print(f"   Response: {content}")
                        except:
                            pass
                    passed += 1
                else:
                    print(f"   ❌ FAIL - Expected {test['expected']}, got {response.status_code}")
                    print(f"   Error: {response.text}")
                    failed += 1
                    
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if passed == len(tests):
        print("🎉 All tests passed! OpenAI client compatibility confirmed.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")

if __name__ == "__main__":
    asyncio.run(test_comprehensive())
