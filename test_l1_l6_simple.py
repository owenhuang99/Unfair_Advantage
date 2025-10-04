#!/usr/bin/env python3
"""
Simple test script for L1-L6 implementation
"""

from core import process_new_link

def test_simple_l1_l6():
    """Test that L1-L6 are generated properly"""
    test_url = "https://docs.python.org/3/tutorial/introduction.html"

    print(f"🧠 Testing L1-L6 on: {test_url}")
    print("This will make an actual API call...")

    try:
        result = process_new_link(test_url)

        if result["success"]:
            print("✅ Successfully processed article!")

            link_data = result["link_data"]
            print(f"📄 Article title: {link_data.get('headline', 'N/A')}")

            # Show L1-L6 hierarchical tags
            print(f"📊 L1-L6 Hierarchical Tags:")
            hierarchy_parts = []
            for level in ["L1", "L2", "L3", "L4", "L5", "L6"]:
                value = link_data.get(level)
                if value:
                    if isinstance(value, list):
                        # L3-L6 are arrays
                        if value:
                            display_value = ", ".join(str(v) for v in value)
                            hierarchy_parts.append(f"{level}: [{display_value}]")
                    else:
                        # L1-L2 are single strings
                        if str(value).strip():
                            hierarchy_parts.append(f"{level}: {value}")

            if hierarchy_parts:
                print(f"  🔸 {' → '.join(hierarchy_parts)}")
            else:
                print("  ⚠️  No hierarchical tags generated")

            # Show raw L1-L6 data
            l1_l6_data = {k: v for k, v in link_data.items() if k in ["L1", "L2", "L3", "L4", "L5", "L6"]}
            print(f"🔍 Raw L1-L6 data: {l1_l6_data}")

        else:
            print(f"❌ Error: {result['error']}")

    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Simple L1-L6 Implementation\n")
    test_simple_l1_l6()
    print("\n✨ Test complete!")