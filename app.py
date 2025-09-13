import streamlit as st
import re
from core import process_new_link, mark_card_status, load_all_unlearned_cards, generate_cards_for_url, reset_learned, canonicalize_url,load_unlearned_cards,load_csv


st.set_page_config(page_title="Link Learning App", layout="wide")

# --- Sidebar navigation ---
page = st.sidebar.radio("Navigation", ["Add Links", "Review Cards"])


# --- Helper fuctions ---

# Filter DataFrame
def has_any(selected, cell):
    if not selected:
        return True
    if isinstance(cell, list):
        return any(item in cell for item in selected)
    return False

def clean_tldr(tldr):
    if isinstance(tldr, list):
        # Remove extra quotes and join with newlines
        return "\n".join(str(item).replace('"', '').strip() for item in tldr)
    elif isinstance(tldr, str):
        # If it's a string, try to split by common separators
        return "\n".join([s.strip().replace('"', '') for s in re.split(r'[\n•\-]+', tldr) if s.strip()])
    else:
        return str(tldr)
    

# --- Session state for flashcard queue logic ---
if "main_q" not in st.session_state:
    st.session_state.main_q = []
if "again_q" not in st.session_state:
    st.session_state.again_q = []
if "round_idx" not in st.session_state:
    st.session_state.round_idx = 1
if "total_start" not in st.session_state:
    st.session_state.total_start = 0
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "last_url" not in st.session_state:
    st.session_state.last_url = ""


# if page == "Add Links":
#     st.title("Add New Link")

#     df_links = load_csv()  # loads links_store.csv

#     # --- Add new link ---
#     url = st.text_input("Enter URL:")
#     process_clicked = st.button("Process Link")

#     if not process_clicked:
#         # Historic table filters
#         all_categories = sorted({cat for cats in df_links["categories"] for cat in (cats if isinstance(cats, list) else [])})
#         all_tags = sorted({tag for tags in df_links["tags"] for tag in (tags if isinstance(tags, list) else [])})

#         col_cat, col_tag = st.columns(2)
#         with col_cat:
#             selected_categories = st.multiselect("Filter by Category", options=all_categories, key="historic_cat")
#         with col_tag:
#             selected_tags = st.multiselect("Filter by Tag", options=all_tags, key="historic_tag")

#         df_links_filtered = df_links[
#             df_links["categories"].apply(lambda x: has_any(selected_categories, x)) &
#             df_links["tags"].apply(lambda x: has_any(selected_tags, x))
#         ].copy()
#         df_links_filtered["tldr"] = df_links_filtered["tldr"].apply(clean_tldr)
#         show_cols = ["headline", "url", "categories", "tags", "author", "tldr", "publish_date"]
#         st.subheader("Historic Links")
#         st.dataframe(df_links_filtered[show_cols], use_container_width=True)
#     if process_clicked:
#         with st.spinner("Processing..."):
#             result = process_new_link(url)
#         if result["success"]:
#             st.success("Link processed successfully!")
#             st.session_state.last_url = url

#             # Reload and show updated table (filtered)
#             df_links = load_csv()
#             all_categories = sorted({cat for cats in df_links["categories"] for cat in (cats if isinstance(cats, list) else [])})
#             all_tags = sorted({tag for tags in df_links["tags"] for tag in (tags if isinstance(tags, list) else [])})

#             # Updated table filters (new keys!)
#             col_cat, col_tag = st.columns(2)
#             with col_cat:
#                 selected_categories_new = st.multiselect("Filter by Category", options=all_categories, key="updated_cat")
#             with col_tag:
#                 selected_tags_new = st.multiselect("Filter by Tag", options=all_tags, key="updated_tag")

#             df_links_display = df_links.copy()
#             df_links_display["tldr"] = df_links_display["tldr"].apply(clean_tldr)
#             df_links_filtered = df_links_display[
#                 df_links_display["categories"].apply(lambda x: has_any(selected_categories_new, x)) &
#                 df_links_display["tags"].apply(lambda x: has_any(selected_tags_new, x))
#             ].copy()
#             show_cols = ["headline", "url", "categories", "tags", "author", "tldr", "publish_date"]
#             st.subheader("Updated Links Table")
#             st.dataframe(df_links_filtered[show_cols], use_container_width=True)

#             # Display link data and flashcards as before...
#             st.subheader("Link Analysis")
#             link_data = result["link_data"]
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.write("**Title:**", link_data["headline"])
#                 st.write("**Categories:**", ", ".join(link_data["categories"]))
#                 st.write("**Tags:**", ", ".join(link_data["tags"]))
#             with col2:
#                 st.write("**Author:**", link_data["author"] or "Not found")
#                 st.write("**Published:**", link_data["publish_date"] or "Not found")
#             st.subheader("TLDR")
#             for point in link_data["tldr"]:
#                 st.markdown(f"• {point}")
#             if result["cards"]:
#                 st.subheader("Generated Flashcards")
#                 for card in result["cards"]:
#                     with st.expander(f"Card: {card['question'][:80]}..."):
#                         st.write("**Question:**", card["question"])
#                         st.write("**Answer:**", card["answer"])
#         else:
#             st.error(f"Error processing link: {result['error']}")

if page == "Add Links":
    st.title("Add New Link")

    df_links = load_csv()  # loads links_store.csv

    # --- Add new link ---
    url = st.text_input("Enter URL:")
    # Use session state to persist process_clicked
    if "process_clicked" not in st.session_state:
        st.session_state.process_clicked = False

    if st.button("Process Link"):
        st.session_state.process_clicked = True
        with st.spinner("Processing..."):
            result = process_new_link(url)
        if result["success"]:
            st.success("Link processed successfully!")
            st.session_state.last_url = url
            st.session_state.result = result
        else:
            st.error(f"Error processing link: {result['error']}")
            st.session_state.result = None

    # --- Table filters ---
    if not st.session_state.process_clicked:
        # Historic table filters
        all_categories = sorted({cat for cats in df_links["categories"] for cat in (cats if isinstance(cats, list) else [])})
        all_tags = sorted({tag for tags in df_links["tags"] for tag in (tags if isinstance(tags, list) else [])})

        col_cat, col_tag = st.columns(2)
        with col_cat:
            selected_categories = st.multiselect("Filter by Category", options=all_categories, key="historic_cat")
        with col_tag:
            selected_tags = st.multiselect("Filter by Tag", options=all_tags, key="historic_tag")

        df_links_filtered = df_links[
            df_links["categories"].apply(lambda x: has_any(selected_categories, x)) &
            df_links["tags"].apply(lambda x: has_any(selected_tags, x))
        ].copy()
        df_links_filtered["tldr"] = df_links_filtered["tldr"].apply(clean_tldr)
        show_cols = ["headline", "url", "categories", "tags", "author", "tldr", "publish_date"]
        st.subheader("Historic Links")
        st.dataframe(df_links_filtered[show_cols], use_container_width=True)
    else:
        # Updated table filters (new keys!)
        df_links = load_csv()
        all_categories = sorted({cat for cats in df_links["categories"] for cat in (cats if isinstance(cats, list) else [])})
        all_tags = sorted({tag for tags in df_links["tags"] for tag in (tags if isinstance(tags, list) else [])})

        col_cat, col_tag = st.columns(2)
        with col_cat:
            selected_categories_new = st.multiselect("Filter by Category", options=all_categories, key="updated_cat")
        with col_tag:
            selected_tags_new = st.multiselect("Filter by Tag", options=all_tags, key="updated_tag")

        df_links_display = df_links.copy()
        df_links_display["tldr"] = df_links_display["tldr"].apply(clean_tldr)
        df_links_filtered = df_links_display[
            df_links_display["categories"].apply(lambda x: has_any(selected_categories_new, x)) &
            df_links_display["tags"].apply(lambda x: has_any(selected_tags_new, x))
        ].copy()
        show_cols = ["headline", "url", "categories", "tags", "author", "tldr", "publish_date"]
        st.subheader("Updated Links Table")
        st.dataframe(df_links_filtered[show_cols], use_container_width=True)

        # Display link data and flashcards as before...
        result = st.session_state.get("result")
        if result and result["success"]:
            st.subheader("Link Analysis")
            link_data = result["link_data"]
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Title:**", link_data["headline"])
                st.write("**Categories:**", ", ".join(link_data["categories"]))
                st.write("**Tags:**", ", ".join(link_data["tags"]))
            with col2:
                st.write("**Author:**", link_data["author"] or "Not found")
                st.write("**Published:**", link_data["publish_date"] or "Not found")
            st.subheader("TLDR")
            for point in link_data["tldr"]:
                st.markdown(f"• {point}")
            if result["cards"]:
                st.subheader("Generated Flashcards")
                for card in result["cards"]:
                    with st.expander(f"Card: {card['question'][:80]}..."):
                        st.write("**Question:**", card["question"])
                        st.write("**Answer:**", card["answer"])

    # Optionally, add a "Reset" button to go back to Historic Links
    if st.session_state.process_clicked:
        if st.button("Reset to Historic Links"):
            st.session_state.process_clicked = False
            st.session_state.result = None

elif page == "Review Cards":
    st.title("Review Flashcards")

    # --- Expandable Session Settings ---
    with st.expander("**Session Settings**", expanded=False):
        col_reset, col_learn = st.columns(2)

        # --- Reset scope (left column) ---
        with col_reset:
            st.markdown("**Reset learning progress**")
            reset_scope = st.radio("Reset scope - all learned flashcards will be reset to unlearned", ["All URLs", "Last Added URL"], key="reset_scope")
            if reset_scope == "Last Added URL":
                reset_url = st.session_state.last_url
                st.info(f"Will reset only for: {reset_url or '(none entered yet)'}")
            else:
                reset_url = None
            reset_clicked = st.button("Reset Learning Progress")
            if reset_clicked:
                if reset_scope == "All URLs":
                    reset_learned(
                        url_canonical="",  # ignored when scope is "all"
                        reset_learn_scope="all"
                    )
                elif reset_scope == "Last Added URL" and reset_url:
                    reset_learned(
                        url_canonical=canonicalize_url(reset_url),
                        reset_learn_scope="url"
                    )
                # After reset, reload cards for current learning scope
                if "learn_scope" in st.session_state and st.session_state.learn_scope == "Last Added URL" and st.session_state.last_url:
                    df = load_unlearned_cards(canonicalize_url(st.session_state.last_url))
                else:
                    df = load_all_unlearned_cards()
                cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
                import random
                random.shuffle(cards)
                st.session_state.main_q = cards
                st.session_state.again_q = []
                st.session_state.round_idx = 1
                st.session_state.total_start = len(cards)
                if cards:
                    st.session_state.current_card = cards[0]
                    st.session_state.show_answer = False
                else:
                    st.session_state.current_card = None
        # --- Learning scope (right column) ---
        with col_learn:
            st.markdown("**Review flashcards for**")
            learn_scope = st.radio("Learning scope - choose the scope of the flashcards you want to focus on", ["All URLs", "Last Added URL"], key="learn_scope")
            if learn_scope == "Last Added URL":
                learn_url = st.session_state.last_url
                st.info(f"Will review only for: {learn_url or '(none entered yet)'}")
            else:
                learn_url = None
            set_scope_clicked = st.button("Set Learning Scope")
            if set_scope_clicked:
                # st.session_state.learn_scope = learn_scope
                if learn_scope == "All URLs":
                    df = load_all_unlearned_cards()
                elif learn_scope == "Last Added URL" and learn_url:
                    df = load_unlearned_cards(canonicalize_url(learn_url))
                else:
                    df = load_all_unlearned_cards()
                cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
                import random
                random.shuffle(cards)
                st.session_state.main_q = cards
                st.session_state.again_q = []
                st.session_state.round_idx = 1
                st.session_state.total_start = len(cards)
                if cards:
                    st.session_state.current_card = cards[0]
                    st.session_state.show_answer = False
                else:
                    st.session_state.current_card = None

    # --- Always show first card if available ---
    if st.session_state.current_card is None:
        # Load default (all URLs) if not set
        df = load_all_unlearned_cards()
        cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
        if cards:
            st.session_state.main_q = cards
            st.session_state.again_q = []
            st.session_state.round_idx = 1
            st.session_state.total_start = len(cards)
            st.session_state.current_card = cards[0]
            st.session_state.show_answer = False

    # --- Progress subtitle ---
    if st.session_state.total_start > 0:
        # progress bar
        total = st.session_state.total_start
        left = len(st.session_state.main_q)
        done = total - left
        if total > 0:
            st.markdown(
                f"<div style='margin-bottom:8px; font-size:1.5em;'>Progress: <b>{done}/{total}</b></div>",
                unsafe_allow_html=True
            )
            st.progress(done / total)

        st.markdown(
            f"<div style='color:#666'>Round {st.session_state.round_idx} • "
            f"{len(st.session_state.main_q)} left in this round"
            f"{' • ' + str(len(st.session_state.again_q)) + ' deferred' if len(st.session_state.again_q) else ''}"
            f"{f' • {st.session_state.total_start} total' if st.session_state.total_start else ''}"
            f"</div>",
            unsafe_allow_html=True
        )
    # --- Card display ---
    if st.session_state.current_card:
        card = st.session_state.current_card
        st.markdown("---")
        st.subheader("Question")
        st.markdown(f"**{card['question']}**")

        if not st.session_state.show_answer:
            if st.button("Reveal Answer"):
                st.session_state.show_answer = True

        if st.session_state.show_answer:
            st.subheader("Answer")
            st.markdown(card["answer"])

            colA, colB = st.columns(2)
            with colA:
                if st.button("I Know This 👍"):
                    mark_card_status(card["card_id"], True)
                    if st.session_state.main_q and st.session_state.main_q[0]["card_id"] == card["card_id"]:
                        st.session_state.main_q.pop(0)
                    if not st.session_state.main_q and st.session_state.again_q:
                        st.session_state.main_q = st.session_state.again_q
                        st.session_state.again_q = []
                        st.session_state.round_idx += 1
                    if st.session_state.main_q:
                        st.session_state.current_card = st.session_state.main_q[0]
                        st.session_state.show_answer = False
                    else:
                        st.session_state.current_card = None
                    st.rerun()
            with colB:
                if st.button("Review Again 🔁"):
                    if st.session_state.main_q and st.session_state.main_q[0]["card_id"] == card["card_id"]:
                        st.session_state.again_q.append(st.session_state.main_q.pop(0))
                    if not st.session_state.main_q and st.session_state.again_q:
                        st.session_state.main_q = st.session_state.again_q
                        st.session_state.again_q = []
                        st.session_state.round_idx += 1
                    if st.session_state.main_q:
                        st.session_state.current_card = st.session_state.main_q[0]
                        st.session_state.show_answer = False
                    else:
                        st.session_state.current_card = None
                    st.rerun()
    else:
        st.info("No cards to review! Add links first.")
    # # --- Automatically show first card if available ---
    # df = load_all_unlearned_cards()
    # cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
    # if st.session_state.current_card is None and st.session_state.main_q:
    #     st.session_state.current_card = cards[0]
    #     # st.session_state.current_card = st.session_state.main_q[0]
    #     # st.session_state.show_answer = False



    # # --- Progress subtitle ---
    # if st.session_state.total_start > 0:
    #     st.markdown(
    #         f"<div style='color:#666'>Round {st.session_state.round_idx} • "
    #         f"{len(st.session_state.main_q)} left in this round"
    #         f"{' • ' + str(len(st.session_state.again_q)) + ' deferred' if len(st.session_state.again_q) else ''}"
    #         f"{f' • {st.session_state.total_start} total' if st.session_state.total_start else ''}"
    #         f"</div>",
    #         unsafe_allow_html=True
    #     )
    # # --- Card display ---
    # if st.session_state.current_card:
    #     card = st.session_state.current_card
    #     st.markdown("---")
    #     st.subheader("Question")
    #     st.markdown(f"**{card['question']}**")

    #     if not st.session_state.show_answer:
    #         if st.button("Reveal Answer"):
    #             st.session_state.show_answer = True

    #     if st.session_state.show_answer:
    #         st.subheader("Answer")
    #         st.markdown(card["answer"])

    #         colA, colB = st.columns(2)
    #         with colA:
    #             if st.button("I Know This 👍"):
    #                 mark_card_status(card["card_id"], True)
    #                 # Remove from main_q
    #                 if st.session_state.main_q and st.session_state.main_q[0]["card_id"] == card["card_id"]:
    #                     st.session_state.main_q.pop(0)
    #                 # Rollover logic
    #                 if not st.session_state.main_q and st.session_state.again_q:
    #                     st.session_state.main_q = st.session_state.again_q
    #                     st.session_state.again_q = []
    #                     st.session_state.round_idx += 1
    #                 # Next card
    #                 if st.session_state.main_q:
    #                     st.session_state.current_card = st.session_state.main_q[0]
    #                     st.session_state.show_answer = False
    #                 else:
    #                     st.session_state.current_card = None
    #                 st.experimental_rerun()
    #         with colB:
    #             if st.button("Review Again 🔁"):
    #                 if st.session_state.main_q and st.session_state.main_q[0]["card_id"] == card["card_id"]:
    #                     st.session_state.again_q.append(st.session_state.main_q.pop(0))
    #                 # Rollover logic
    #                 if not st.session_state.main_q and st.session_state.again_q:
    #                     st.session_state.main_q = st.session_state.again_q
    #                     st.session_state.again_q = []
    #                     st.session_state.round_idx += 1
    #                 # Next card
    #                 if st.session_state.main_q:
    #                     st.session_state.current_card = st.session_state.main_q[0]
    #                     st.session_state.show_answer = False
    #                 else:
    #                     st.session_state.current_card = None
    #                 st.experimental_rerun()
    # else:
    #     if st.session_state.total_start > 0:
    #         st.success("All cards learned or deferred round(s) completed. 🎉")
    #     else:
    #         st.info("No cards to review! Add links first.")


    # # --- Settings section ---
    # st.markdown("---")
    # st.subheader("Session Settings")
    # col_reset, col_learn = st.columns(2)

    # # --- Reset scope (left column) ---
    # with col_reset:
    #     st.markdown("**Reset learning progress**")
    #     reset_scope = st.radio("Reset scope", ["All URLs", "Last Added URL"], key="reset_scope")
    #     if reset_scope == "Last Added URL":
    #         reset_url = st.session_state.last_url
    #         st.info(f"Will reset only for: {reset_url or '(none entered yet)'}")
    #     else:
    #         reset_url = None
    #     if st.button("Reset Learning Progress"):
    #         # Reset learning if requested
    #         if reset_scope == "All URLs":
    #             reset_learned(
    #                 url_canonical="",  # ignored when scope is "all"
    #                 reset_learn_scope="all"
    #             )
    #         elif reset_scope == "Last Added URL" and reset_url:
    #             reset_learned(
    #                 url_canonical=canonicalize_url(reset_url),
    #                 reset_learn_scope="url"
    #             )

    # # --- Learning scope (right column) ---
    # with col_learn:
    #     st.markdown("**Review flashcards for**")
    #     learn_scope = st.radio("Learning scope", ["All URLs", "Last Added URL"], key="learn_scope")
    #     if learn_scope == "Last Added URL":
    #         learn_url = st.session_state.last_url
    #         st.info(f"Will review only for: {learn_url or '(none entered yet)'}")
    #     else:
    #         learn_url = None

    #     # --- Start/Restart Session ---
    #     if st.button("Set Learning Scope"):
    #         # Load cards for selected learning scope
    #         if learn_scope == "All URLs":
    #             df = load_all_unlearned_cards()
    #         elif learn_scope == "Last Added URL" and learn_url:
    #             df = load_unlearned_cards(canonicalize_url(learn_url))
    #         else:
    #             df = load_all_unlearned_cards()

    #         cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
    #         import random
    #         random.shuffle(cards)
    #         st.session_state.main_q = cards
    #         st.session_state.again_q = []
    #         st.session_state.round_idx = 1
    #         st.session_state.total_start = len(cards)
    #         # --- Automatically show first card if available ---
    #         if cards:
    #             st.session_state.current_card = cards[0]
    #             st.session_state.show_answer = False
    #         else:
    #             st.session_state.current_card = None


    # # --- Automatically show first card if available ---
    # if st.session_state.current_card is None and st.session_state.main_q:
    #     st.session_state.current_card = st.session_state.main_q[0]
    #     st.session_state.show_answer = False




# Add footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with Owen Huang")
