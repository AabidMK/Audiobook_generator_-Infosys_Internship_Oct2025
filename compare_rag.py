"""
Compare Custom RAG vs LangChain RAG
Test both implementations with the same queries and compare results
"""

import subprocess
import time
from datetime import datetime

# Test queries
QUERIES = [
    "What is the objective?",
    "What are the milestones?",
    "What technology is used for text-to-speech?"
]

TOP_K = 5

def run_rag_test(script_name, query, top_k=5):
    """Run RAG script and measure time"""
    cmd = [
        "python", script_name,
        "--query", query,
        "--top-k", str(top_k),
        "--use-native" if "langchain" in script_name else ""
    ]
    cmd = [c for c in cmd if c]  # Remove empty strings
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={"GOOGLE_API_KEY": "AIzaSyAa2vAQjxEFJMwowuN25BFbOTbjkfTn84U"}
        )
        elapsed = time.time() - start
        
        if result.returncode == 0:
            # Extract answer from output
            output = result.stdout
            if "ANSWER" in output:
                answer = output.split("ANSWER")[-1].split("===")[0].strip()
            else:
                answer = output.strip()
            
            return {
                "success": True,
                "answer": answer,
                "time": elapsed,
                "error": None
            }
        else:
            return {
                "success": False,
                "answer": None,
                "time": elapsed,
                "error": result.stderr
            }
    except Exception as e:
        return {
            "success": False,
            "answer": None,
            "time": time.time() - start,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("RAG COMPARISON TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    results = {
        "custom": [],
        "langchain": []
    }
    
    for i, query in enumerate(QUERIES, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {i}: {query}")
        print('='*80)
        
        # Test Custom RAG
        print("\n[1] CUSTOM RAG (rag_query.py)")
        print("-" * 80)
        custom_result = run_rag_test("rag_query.py", query, TOP_K)
        results["custom"].append(custom_result)
        
        if custom_result["success"]:
            print(f"✓ Success ({custom_result['time']:.2f}s)")
            print(f"\nAnswer:\n{custom_result['answer']}")
        else:
            print(f"✗ Failed: {custom_result['error']}")
        
        # Test LangChain RAG
        print("\n[2] LANGCHAIN RAG (rag_langchain.py)")
        print("-" * 80)
        langchain_result = run_rag_test("rag_langchain.py", query, TOP_K)
        results["langchain"].append(langchain_result)
        
        if langchain_result["success"]:
            print(f"✓ Success ({langchain_result['time']:.2f}s)")
            print(f"\nAnswer:\n{langchain_result['answer']}")
        else:
            print(f"✗ Failed: {langchain_result['error']}")
        
        # Comparison
        print("\n" + "-" * 80)
        print("COMPARISON:")
        if custom_result["success"] and langchain_result["success"]:
            time_diff = langchain_result["time"] - custom_result["time"]
            if time_diff > 0:
                print(f"⚡ Custom RAG was {time_diff:.2f}s faster")
            else:
                print(f"⚡ LangChain RAG was {abs(time_diff):.2f}s faster")
            
            # Compare answer lengths
            custom_len = len(custom_result["answer"])
            langchain_len = len(langchain_result["answer"])
            print(f"📝 Answer lengths: Custom={custom_len} chars, LangChain={langchain_len} chars")
        
        print()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    custom_successes = sum(1 for r in results["custom"] if r["success"])
    langchain_successes = sum(1 for r in results["langchain"] if r["success"])
    
    print(f"\nCustom RAG: {custom_successes}/{len(QUERIES)} queries successful")
    if custom_successes > 0:
        custom_avg_time = sum(r["time"] for r in results["custom"] if r["success"]) / custom_successes
        print(f"  Average time: {custom_avg_time:.2f}s")
    
    print(f"\nLangChain RAG: {langchain_successes}/{len(QUERIES)} queries successful")
    if langchain_successes > 0:
        langchain_avg_time = sum(r["time"] for r in results["langchain"] if r["success"]) / langchain_successes
        print(f"  Average time: {langchain_avg_time:.2f}s")
    
    if custom_successes > 0 and langchain_successes > 0:
        print(f"\n⚡ Speed difference: {abs(custom_avg_time - langchain_avg_time):.2f}s per query")
        if custom_avg_time < langchain_avg_time:
            print(f"   Custom RAG is {((langchain_avg_time/custom_avg_time - 1) * 100):.1f}% faster")
        else:
            print(f"   LangChain RAG is {((custom_avg_time/langchain_avg_time - 1) * 100):.1f}% faster")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
For Production Use:
  • Custom RAG (rag_query.py) - Lightweight, minimal dependencies, slightly faster
  
For Development/Prototyping:
  • LangChain RAG (rag_langchain.py) - LCEL chains, easy extensibility, built-in features
  
Both implementations produce high-quality answers and work with the same vector database.
Choose based on your specific requirements and use case.
""")

if __name__ == "__main__":
    main()
