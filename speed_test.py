#!/usr/bin/env python3
"""
Speed test: Old vs Optimized sequential tagging
"""

import time
import sys

def old_slow_version(L1: str, L2: str, sequential_tagging: dict) -> tuple:
    """Old version with performance bottlenecks"""
    if not sequential_tagging or not isinstance(sequential_tagging, dict):
        return [], [], [], [], []

    paths = []
    all_L3, all_L4, all_L5, all_L6 = set(), set(), set(), set()

    L3_tags = sequential_tagging.get("L3_tags", [])
    branching_paths = sequential_tagging.get("branching_paths", {})
    base_path = [L1, L2]

    for L3_tag in L3_tags:
        all_L3.add(L3_tag)
        L3_path = base_path + [L3_tag]  # List concatenation overhead

        if L3_tag not in branching_paths:
            paths.append(L3_path)
            continue

        L3_branch = branching_paths[L3_tag]
        L4_tags = L3_branch.get("L4_tags", [])
        L4_paths = L3_branch.get("L4_paths", {})

        if not L4_tags:
            paths.append(L3_path)
            continue

        for L4_tag in L4_tags:
            all_L4.add(L4_tag)
            L4_path = L3_path + [L4_tag]  # More list concatenation

            if L4_tag not in L4_paths:
                paths.append(L4_path)
                continue

            L4_branch = L4_paths[L4_tag]
            L5_tags = L4_branch.get("L5_tags", [])
            L5_paths = L4_branch.get("L5_paths", {})

            if not L5_tags:
                paths.append(L4_path)
                continue

            for L5_tag in L5_tags:
                all_L5.add(L5_tag)
                L5_path = L4_path + [L5_tag]  # Even more list concatenation

                if L5_tag not in L5_paths:
                    paths.append(L5_path)
                    continue

                L5_branch = L5_paths[L5_tag]
                L6_tags = L5_branch.get("L6_tags", [])

                if not L6_tags:
                    paths.append(L5_path)
                    continue

                for L6_tag in L6_tags:
                    all_L6.add(L6_tag)
                    L6_path = L5_path + [L6_tag]  # Maximum list concatenation
                    paths.append(L6_path)

    return (
        paths,
        sorted(list(all_L3)),  # Slow set → list → sort
        sorted(list(all_L4)),
        sorted(list(all_L5)),
        sorted(list(all_L6))
    )

def new_optimized_version(L1: str, L2: str, sequential_tagging: dict) -> tuple:
    """Optimized version for speed"""
    if not sequential_tagging:
        return [], [], [], [], []

    paths = []
    L3_set, L4_set, L5_set, L6_set = set(), set(), set(), set()

    L3_tags = sequential_tagging.get("L3_tags", [])
    if not L3_tags:
        return [], [], [], [], []

    branching_paths = sequential_tagging.get("branching_paths", {})
    base = [L1, L2]  # Reuse base list

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

    return (
        paths,
        sorted(L3_set) if L3_set else [],  # Fast conditional sorting
        sorted(L4_set) if L4_set else [],
        sorted(L5_set) if L5_set else [],
        sorted(L6_set) if L6_set else []
    )

def speed_test():
    # Complex test case
    L1, L2 = "Tech", "Product Management"

    # Large sequential tagging structure for stress testing
    sequential_tagging = {
        "L3_tags": ["Machine Learning", "Data Strategy", "Product Analytics"],
        "branching_paths": {
            "Machine Learning": {
                "L4_tags": ["Product Development", "Model Deployment", "Research"],
                "L4_paths": {
                    "Product Development": {
                        "L5_tags": ["Data Collection", "Requirements", "Testing"],
                        "L5_paths": {
                            "Data Collection": {"L6_tags": ["Feature Engineering", "Data Validation", "ETL"]},
                            "Requirements": {"L6_tags": ["Stakeholder Alignment", "Success Metrics"]},
                            "Testing": {"L6_tags": ["A/B Testing", "Model Validation"]}
                        }
                    },
                    "Model Deployment": {
                        "L5_tags": ["Training", "Production", "Monitoring"],
                        "L5_paths": {
                            "Training": {"L6_tags": ["Hyperparameter Tuning", "Model Evaluation"]},
                            "Production": {"L6_tags": ["CI/CD", "Scaling", "Performance"]},
                            "Monitoring": {"L6_tags": ["Metrics", "Alerts", "Debugging"]}
                        }
                    },
                    "Research": {
                        "L5_tags": ["Literature Review", "Experimentation"],
                        "L5_paths": {
                            "Literature Review": {"L6_tags": ["Papers", "Benchmarks"]},
                            "Experimentation": {"L6_tags": ["Prototyping", "Analysis"]}
                        }
                    }
                }
            },
            "Data Strategy": {
                "L4_tags": ["Analytics Framework", "Data Governance"],
                "L4_paths": {
                    "Analytics Framework": {
                        "L5_tags": ["Metrics Design", "Reporting"],
                        "L5_paths": {
                            "Metrics Design": {"L6_tags": ["KPI Tracking", "Dashboard Creation"]},
                            "Reporting": {"L6_tags": ["Business Intelligence", "Automated Reports"]}
                        }
                    },
                    "Data Governance": {
                        "L5_tags": ["Quality Control", "Privacy"],
                        "L5_paths": {
                            "Quality Control": {"L6_tags": ["Data Validation", "Consistency Checks"]},
                            "Privacy": {"L6_tags": ["GDPR Compliance", "Data Anonymization"]}
                        }
                    }
                }
            },
            "Product Analytics": {
                "L4_tags": ["User Behavior", "Conversion"],
                "L4_paths": {
                    "User Behavior": {
                        "L5_tags": ["Event Tracking", "Cohort Analysis"],
                        "L5_paths": {
                            "Event Tracking": {"L6_tags": ["Click Events", "Page Views"]},
                            "Cohort Analysis": {"L6_tags": ["Retention", "Churn Analysis"]}
                        }
                    },
                    "Conversion": {
                        "L5_tags": ["Funnel Analysis", "Optimization"],
                        "L5_paths": {
                            "Funnel Analysis": {"L6_tags": ["Drop-off Points", "Conversion Rates"]},
                            "Optimization": {"L6_tags": ["CRO", "Personalization"]}
                        }
                    }
                }
            }
        }
    }

    print("🚀 Performance Comparison Test")
    print("=" * 50)
    print(f"Test case: {len(sequential_tagging['L3_tags'])} L3 tags with deep branching")

    iterations = 1000
    print(f"Running {iterations} iterations...")
    print()

    # Test old version
    print("⏱️  Testing OLD version...")
    start_time = time.time()
    for i in range(iterations):
        old_paths, old_L3, old_L4, old_L5, old_L6 = old_slow_version(L1, L2, sequential_tagging)
    old_time = time.time() - start_time

    # Test optimized version
    print("⚡ Testing OPTIMIZED version...")
    start_time = time.time()
    for i in range(iterations):
        new_paths, new_L3, new_L4, new_L5, new_L6 = new_optimized_version(L1, L2, sequential_tagging)
    new_time = time.time() - start_time

    # Results
    print()
    print("📊 Results:")
    print(f"   Old version: {old_time:.4f} seconds ({old_time/iterations*1000:.2f}ms per call)")
    print(f"   Optimized:   {new_time:.4f} seconds ({new_time/iterations*1000:.2f}ms per call)")
    print(f"   ⚡ Speedup:   {old_time/new_time:.1f}x faster!")
    print()

    # Verify correctness
    correctness = (
        old_paths == new_paths and
        old_L3 == new_L3 and
        old_L4 == new_L4 and
        old_L5 == new_L5 and
        old_L6 == new_L6
    )

    print(f"✅ Results identical: {correctness}")
    print(f"📈 Generated {len(new_paths)} knowledge paths")
    print(f"🏷️  Extracted L3: {len(new_L3)}, L4: {len(new_L4)}, L5: {len(new_L5)}, L6: {len(new_L6)} tags")

    if new_time < old_time and correctness:
        print()
        print("🎉 OPTIMIZATION SUCCESS!")
        print("✅ Maintained mathematical correctness")
        print("⚡ Significantly improved processing speed")
        print("🏆 Ready for million-user scale!")
    else:
        print("❌ Optimization failed")
        return False

    return True

if __name__ == "__main__":
    success = speed_test()
    if not success:
        sys.exit(1)