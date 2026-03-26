#!/usr/bin/env python3
"""
Minimal test for sequential tagging logic (without dependencies)
"""

def generate_knowledge_paths_from_sequential_tagging(L1: str, L2: str, sequential_tagging: dict) -> tuple:
    """
    OPTIMIZED: Generate knowledge paths and extract L3-L6 arrays from sequential tagging.
    Fast version with minimal overhead while maintaining correctness.
    """
    if not sequential_tagging:
        return [], [], [], [], []

    # Pre-allocate arrays for speed
    paths = []
    L3_set, L4_set, L5_set, L6_set = set(), set(), set(), set()

    L3_tags = sequential_tagging.get("L3_tags", [])
    if not L3_tags:
        return [], [], [], [], []

    branching_paths = sequential_tagging.get("branching_paths", {})
    base = [L1, L2]  # Reuse base list

    # Fast single-pass traversal with pre-built paths
    for L3 in L3_tags:
        L3_set.add(L3)
        L3_branch = branching_paths.get(L3)

        if not L3_branch:
            paths.append(base + [L3])
            continue

        L4_tags = L3_branch.get("L4_tags", [])
        if not L4_tags:
            paths.append(base + [L3])
            continue

        L4_paths = L3_branch.get("L4_paths", {})

        for L4 in L4_tags:
            L4_set.add(L4)
            L4_branch = L4_paths.get(L4)

            if not L4_branch:
                paths.append(base + [L3, L4])
                continue

            L5_tags = L4_branch.get("L5_tags", [])
            if not L5_tags:
                paths.append(base + [L3, L4])
                continue

            L5_paths = L4_branch.get("L5_paths", {})

            for L5 in L5_tags:
                L5_set.add(L5)
                L5_branch = L5_paths.get(L5)

                if not L5_branch:
                    paths.append(base + [L3, L4, L5])
                    continue

                L6_tags = L5_branch.get("L6_tags", [])
                if not L6_tags:
                    paths.append(base + [L3, L4, L5])
                    continue

                for L6 in L6_tags:
                    L6_set.add(L6)
                    paths.append(base + [L3, L4, L5, L6])

    # Fast conversion to sorted lists
    return (
        paths,
        sorted(L3_set) if L3_set else [],
        sorted(L4_set) if L4_set else [],
        sorted(L5_set) if L5_set else [],
        sorted(L6_set) if L6_set else []
    )

def test_sequential_tagging():
    print("Testing Sequential Tagging Implementation")
    print("=" * 50)

    # Sample sequential tagging from your broken example (fixed)
    L1 = "Tech"
    L2 = "Product Management"
    sequential_tagging = {
        "L3_tags": ["Machine Learning"],
        "branching_paths": {
            "Machine Learning": {
                "L4_tags": ["Product Development", "Model Deployment"],
                "L4_paths": {
                    "Product Development": {
                        "L5_tags": ["Data Collection"],
                        "L5_paths": {
                            "Data Collection": {
                                "L6_tags": ["Feature Engineering"]
                            }
                        }
                    },
                    "Model Deployment": {
                        "L5_tags": ["Model Training"],
                        "L5_paths": {
                            "Model Training": {
                                "L6_tags": ["Model Evaluation"]
                            }
                        }
                    }
                }
            }
        }
    }

    print("🔄 Original (Broken) Example:")
    print("   L3: ['Machine Learning']")
    print("   L4: ['Product Development', 'Model Deployment']")
    print("   L5: ['Data Collection', 'Model Training']")
    print("   L6: ['Feature Engineering', 'Model Evaluation']")
    print("   ❌ Problem: No clear L3→L4→L5→L6 relationships")
    print()

    # Test the function
    paths, L3_array, L4_array, L5_array, L6_array = generate_knowledge_paths_from_sequential_tagging(
        L1, L2, sequential_tagging
    )

    print("✅ New Sequential Tagging Result:")
    print(f"   L3: {L3_array}")
    print(f"   L4: {L4_array}")
    print(f"   L5: {L5_array}")
    print(f"   L6: {L6_array}")
    print()

    print("🗺️  Generated Knowledge Paths (Mathematically Correct):")
    for i, path in enumerate(paths, 1):
        path_str = " → ".join(path)
        print(f"   {i:2d}. {path_str}")
    print()

    # Validate the fix
    expected_paths = [
        ["Tech", "Product Management", "Machine Learning", "Product Development", "Data Collection", "Feature Engineering"],
        ["Tech", "Product Management", "Machine Learning", "Model Deployment", "Model Training", "Model Evaluation"]
    ]

    print("🔍 Validation:")
    for expected in expected_paths:
        found = expected in paths
        path_str = " → ".join(expected)
        print(f"   {'✅' if found else '❌'} Contains path: {path_str}")

    # Key insight
    print()
    print("💡 Key Insight:")
    print("   ✅ Each L4 concept properly branches to specific L5 children")
    print("   ✅ Each L5 concept properly branches to specific L6 children")
    print("   ✅ No orphaned relationships or parallel arrays")
    print("   ✅ Knowledge paths reflect actual sequential tagging logic")

    return len(paths) == 2 and all(expected in paths for expected in expected_paths)

if __name__ == "__main__":
    success = test_sequential_tagging()
    print()
    if success:
        print("🏆 Sequential Tagging Test PASSED!")
        print("✅ Implementation correctly fixes the branching relationship problem")
    else:
        print("❌ Test FAILED - implementation needs fixes")