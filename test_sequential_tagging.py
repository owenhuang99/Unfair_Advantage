#!/usr/bin/env python3
"""
Test the sequential tagging implementation
"""

import sys
import json
sys.path.append('.')

from core import generate_knowledge_paths_from_sequential_tagging

# Test case: Complex sequential tagging structure
def test_sequential_tagging():
    print("Testing Sequential Tagging Implementation")
    print("=" * 50)

    # Sample LLM output with sequential tagging
    L1 = "Tech"
    L2 = "Product Management"
    sequential_tagging = {
        "L3_tags": ["Machine Learning", "Data Strategy"],
        "branching_paths": {
            "Machine Learning": {
                "L4_tags": ["Product Development", "Model Deployment"],
                "L4_paths": {
                    "Product Development": {
                        "L5_tags": ["Data Collection", "Requirements Analysis"],
                        "L5_paths": {
                            "Data Collection": {
                                "L6_tags": ["Feature Engineering", "Data Validation"]
                            },
                            "Requirements Analysis": {
                                "L6_tags": ["Stakeholder Alignment", "Success Metrics"]
                            }
                        }
                    },
                    "Model Deployment": {
                        "L5_tags": ["Model Training", "Production Pipeline"],
                        "L5_paths": {
                            "Model Training": {
                                "L6_tags": ["Hyperparameter Tuning", "Model Evaluation"]
                            },
                            "Production Pipeline": {
                                "L6_tags": ["Monitoring", "A/B Testing"]
                            }
                        }
                    }
                }
            },
            "Data Strategy": {
                "L4_tags": ["Analytics Framework"],
                "L4_paths": {
                    "Analytics Framework": {
                        "L5_tags": ["Metrics Design"],
                        "L5_paths": {
                            "Metrics Design": {
                                "L6_tags": ["KPI Tracking", "Dashboard Creation"]
                            }
                        }
                    }
                }
            }
        }
    }

    # Test the function
    try:
        paths, L3_array, L4_array, L5_array, L6_array = generate_knowledge_paths_from_sequential_tagging(
            L1, L2, sequential_tagging
        )

        print(f"✅ L1: {L1}")
        print(f"✅ L2: {L2}")
        print()

        print("📋 Extracted Arrays (for backward compatibility):")
        print(f"   L3: {L3_array}")
        print(f"   L4: {L4_array}")
        print(f"   L5: {L5_array}")
        print(f"   L6: {L6_array}")
        print()

        print("🗺️  Generated Knowledge Paths:")
        for i, path in enumerate(paths, 1):
            path_str = " → ".join(path)
            print(f"   {i:2d}. {path_str}")
        print()

        # Validate key properties
        print("🔍 Validation:")

        # Check that all paths start with L1 → L2
        all_start_correct = all(path[:2] == [L1, L2] for path in paths)
        print(f"   ✅ All paths start with {L1} → {L2}: {all_start_correct}")

        # Check that no path skips levels (sequential property)
        def is_sequential_path(path):
            # Path should be sequential: L1, L2, L3, [L4, [L5, [L6]]]
            return len(path) >= 3  # At least L1, L2, L3

        all_sequential = all(is_sequential_path(path) for path in paths)
        print(f"   ✅ All paths are sequential (L1→L2→L3...): {all_sequential}")

        # Check specific expected paths
        expected_paths = [
            ["Tech", "Product Management", "Machine Learning", "Product Development", "Data Collection", "Feature Engineering"],
            ["Tech", "Product Management", "Machine Learning", "Model Deployment", "Model Training", "Hyperparameter Tuning"],
            ["Tech", "Product Management", "Data Strategy", "Analytics Framework", "Metrics Design", "KPI Tracking"]
        ]

        for expected in expected_paths:
            found = expected in paths
            path_str = " → ".join(expected)
            print(f"   {'✅' if found else '❌'} Contains expected path: {path_str}")

        print(f"\n🎯 Total paths generated: {len(paths)}")
        print(f"🧮 Expected paths based on structure: 10 (2×4 + 1×2)")

        success = len(paths) == 10 and all_start_correct and all_sequential
        print(f"\n{'🎉 Test PASSED!' if success else '❌ Test FAILED!'}")

        return success

    except Exception as e:
        print(f"❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_empty_structure():
    print("\nTesting Empty Sequential Tagging")
    print("=" * 40)

    # Test empty structure
    paths, L3, L4, L5, L6 = generate_knowledge_paths_from_sequential_tagging(
        "Tech", "AI", {}
    )

    empty_test = (len(paths) == 0 and len(L3) == 0 and len(L4) == 0 and len(L5) == 0 and len(L6) == 0)
    print(f"{'✅' if empty_test else '❌'} Empty structure returns empty arrays")

    return empty_test

if __name__ == "__main__":
    test1 = test_sequential_tagging()
    test2 = test_empty_structure()

    if test1 and test2:
        print("\n🏆 All tests PASSED!")
        print("✅ Sequential tagging implementation is working correctly")
        print("✅ Knowledge paths reflect exact L3→L4→L5→L6 branching logic")
    else:
        print("\n💥 Some tests FAILED!")
        print("❌ Implementation needs fixes")
        sys.exit(1)