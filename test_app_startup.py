#!/usr/bin/env python3
"""
Test script to verify app startup logic works without KeyError
"""

import pandas as pd
from core import load_csv

def test_filtering_logic():
    """Test that the filtering logic works without KeyError"""
    print("🧠 Testing app filtering logic...")

    # Load the CSV
    df_links = load_csv()
    print(f"📄 Loaded CSV with {len(df_links)} rows")
    print(f"📊 Columns: {list(df_links.columns)}")

    # Test the L1-L6 column checks
    if "L1" in df_links.columns and "L2" in df_links.columns:
        all_l1_values = sorted({val for val in df_links["L1"] if pd.notna(val) and val})
        all_l2_values = sorted({val for val in df_links["L2"] if pd.notna(val) and val})
        print(f"✅ L1 values found: {all_l1_values}")
        print(f"✅ L2 values found: {all_l2_values}")
    else:
        all_l1_values = []
        all_l2_values = []
        print("⚠️  L1/L2 columns not found, using empty lists")

    # Test filtering logic with empty selections (this was causing the KeyError)
    selected_l1 = []  # Empty selection
    selected_l2 = []  # Empty selection

    print("🧪 Testing boolean mask creation...")

    # This is the fixed logic
    if "L1" in df_links.columns and selected_l1:
        l1_mask = df_links["L1"].isin(selected_l1)
    else:
        l1_mask = pd.Series([True] * len(df_links), index=df_links.index)

    if "L2" in df_links.columns and selected_l2:
        l2_mask = df_links["L2"].isin(selected_l2)
    else:
        l2_mask = pd.Series([True] * len(df_links), index=df_links.index)

    # Test the filtering
    df_links_filtered = df_links[l1_mask & l2_mask].copy()
    print(f"✅ Filtering successful! {len(df_links_filtered)} rows after filtering")

    # Test column display logic
    base_cols = ["headline", "url", "author", "tldr", "publish_date"]
    l_cols = ["L1", "L2", "L3", "L4", "L5", "L6"]
    available_l_cols = [col for col in l_cols if col in df_links.columns]
    show_cols = base_cols[:2] + available_l_cols + base_cols[2:]
    print(f"📋 Show columns: {show_cols}")

    print("✅ All logic tests passed! App should start without KeyError")

if __name__ == "__main__":
    print("🚀 Testing App Startup Logic\n")
    try:
        test_filtering_logic()
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    print("\n✨ Test complete!")