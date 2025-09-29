import streamlit as st
from providers.geocode_osm import search_addresses
from core.normalise import normalise_jsonld
from providers.jsonld_extractor import extract_schema_org

ALLOW_WEB_FETCH = True

st.set_page_config("PropLens MVP")
st.sidebar.header("Property Search")

query = st.sidebar.text_input("Enter address", "")

if query and len(query) > 4:
    suggestions = search_addresses(query)
    choice = st.sidebar.selectbox("Suggestions", suggestions, format_func=lambda x: x.display_name)
    if st.sidebar.button("Find details") and choice:
        st.write("### Property Details")
        st.json(choice.model_dump())

        if ALLOW_WEB_FETCH:
            st.info("Attempting JSON-LD extraction…")
            # Placeholder for portal_finders to generate candidate URLs
            urls = []  # TODO: implement
            for url in urls:
                data = extract_schema_org(url)
                if data:
                    facts = normalise_jsonld(data)
                    st.json(facts)

