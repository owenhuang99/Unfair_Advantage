#!/usr/bin/env python3
"""
Sequential Paths Validation System
Ensures correctness while maintaining speed
"""

def validate_sequential_paths(L1: str, L2: str, sequential_paths: list) -> tuple:
    """
    Validate and process sequential paths with correctness guarantees

    Returns: (knowledge_paths, L3_array, L4_array, L5_array, L6_array, validation_report)
    """
    if not sequential_paths:
        return [], [], [], [], [], {"valid": True, "issues": []}

    # Validation report
    issues = []
    corrected_paths = []

    # Extract unique tags at each level
    L3_set, L4_set, L5_set, L6_set = set(), set(), set(), set()

    for path_idx, path in enumerate(sequential_paths):
        if not isinstance(path, list) or len(path) < 1:
            issues.append(f"Path {path_idx}: Invalid format or empty")
            continue

        # Validate path length (L3 minimum, L3-L6 maximum)
        if len(path) > 4:  # L3, L4, L5, L6 maximum
            issues.append(f"Path {path_idx}: Too long ({len(path)} levels), truncating to 4")
            path = path[:4]

        # Build complete path with L1, L2 prefix
        complete_path = [L1, L2] + path

        # Extract tags by position
        if len(path) >= 1:
            L3_set.add(path[0])
        if len(path) >= 2:
            L4_set.add(path[1])
        if len(path) >= 3:
            L5_set.add(path[2])
        if len(path) >= 4:
            L6_set.add(path[3])

        # Validate sequential logic (optional semantic checks)
        if len(path) >= 2:
            L3, L4 = path[0], path[1]
            if not _is_valid_L3_to_L4_progression(L3, L4):
                issues.append(f"Path {path_idx}: Questionable L3→L4 progression: {L3} → {L4}")

        corrected_paths.append(complete_path)

    # Validation report
    validation_report = {
        "valid": len(issues) == 0,
        "issues": issues,
        "paths_processed": len(corrected_paths),
        "tags_extracted": {
            "L3": len(L3_set),
            "L4": len(L4_set),
            "L5": len(L5_set),
            "L6": len(L6_set)
        }
    }

    return (
        corrected_paths,
        sorted(L3_set),
        sorted(L4_set),
        sorted(L5_set),
        sorted(L6_set),
        validation_report
    )

def _is_valid_L3_to_L4_progression(L3: str, L4: str) -> bool:
    """
    Optional semantic validation of L3→L4 relationships
    Can be enhanced with domain knowledge or ML classification
    """
    # Basic heuristics (can be made more sophisticated)
    L3_lower = L3.lower()
    L4_lower = L4.lower()

    # Some basic rules
    if "machine learning" in L3_lower:
        valid_L4 = ["model", "product", "deployment", "training", "development", "research"]
        return any(term in L4_lower for term in valid_L4)

    if "data" in L3_lower:
        valid_L4 = ["analytics", "collection", "processing", "governance", "pipeline", "strategy"]
        return any(term in L4_lower for term in valid_L4)

    # Default: assume valid (trust LLM)
    return True

# Example usage and test
def test_validation():
    print("🔍 Testing Sequential Paths Validation")
    print("=" * 50)

    # Test case with good and problematic paths
    L1, L2 = "Tech", "Product Management"
    sequential_paths = [
        ["Machine Learning", "Product Development", "Data Collection", "Feature Engineering"],
        ["Machine Learning", "Model Deployment", "Model Training", "Model Evaluation"],
        ["Data Strategy", "Analytics Framework", "Metrics Design"],  # Short path (valid)
        ["Invalid"],  # Too short but acceptable
        ["A", "B", "C", "D", "E", "F"],  # Too long (will be truncated)
        []  # Empty (will be rejected)
    ]

    paths, L3, L4, L5, L6, report = validate_sequential_paths(L1, L2, sequential_paths)

    print("✅ Validation Results:")
    print(f"   Valid: {report['valid']}")
    print(f"   Paths processed: {report['paths_processed']}")
    print(f"   Issues found: {len(report['issues'])}")

    for issue in report['issues']:
        print(f"      ⚠️  {issue}")

    print(f"\n📊 Extracted Tags:")
    print(f"   L3 ({len(L3)}): {L3}")
    print(f"   L4 ({len(L4)}): {L4}")
    print(f"   L5 ({len(L5)}): {L5}")
    print(f"   L6 ({len(L6)}): {L6}")

    print(f"\n🗺️  Final Knowledge Paths ({len(paths)}):")
    for i, path in enumerate(paths, 1):
        print(f"   {i:2d}. {' → '.join(path)}")

    # Key advantages
    print(f"\n💡 Correctness Guarantees:")
    print(f"   ✅ All paths start with {L1} → {L2}")
    print(f"   ✅ No paths exceed 6 levels (L1→L2→L3→L4→L5→L6)")
    print(f"   ✅ Invalid/empty paths filtered out")
    print(f"   ✅ L3-L6 arrays correctly extracted")
    print(f"   ✅ Validation report available for debugging")

    return len(paths) > 0 and report['paths_processed'] >= 3

if __name__ == "__main__":
    success = test_validation()
    print(f"\n{'🏆 Test PASSED!' if success else '❌ Test FAILED!'}")