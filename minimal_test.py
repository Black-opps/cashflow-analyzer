import asyncio
from src.services.analyzer import CashflowAnalyzer

async def test():
    analyzer = CashflowAnalyzer()
    try:
        result = await analyzer.get_summary("12345678-1234-1234-1234-123456789012", 7, "day")
        print(f"Result: {result}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
    finally:
        analyzer.close()

asyncio.run(test())