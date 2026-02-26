from src.graph import build_graph

graph = build_graph()

input_state = {
    "repo_url": "https://github.com/langchain-ai/langgraph",
    "pdf_path": "reports/interim_report.pdf",
    "evidences": {},
    "opinions": []
}

result = graph.invoke(input_state)

print("\n=== FINAL STATE ===\n")
print(result)

print("\n=== EVIDENCE KEYS ===\n")
print(result["evidences"].keys())

print("\n=== FULL EVIDENCE STRUCTURE ===\n")
for key, value in result["evidences"].items():
    print(f"\n{key}:")
    for ev in value:
        print(ev)