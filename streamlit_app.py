import os
import time
import streamlit as st
from typing import Optional

from providers.geocode_osm import search_addresses
from providers.portal_finders import find_candidate_urls
from providers.jsonld_extractor import extract_schema_org
from providers.nsw_open_data import try_open_parcel
from core.normalise import (
    normalise_jsonld,
    estimate_from_heuristics,
    merge_facts,
)
from models.facts import AddressResolved, PropertyFacts, FieldValue
from calculators.stamp_duty import calc_stamp_duty
from calculators.council_rates import calc_council_rates
from calculators.insurance import estimate_sum_insured, premium_from_risk
from calculators.repayments import calc_repayments, pick_active_rate
from calculators.cashflow import calc_cashflow
from utils.pdf_export import generate_pdf

# Feature flag
ALLOW_WEB_FETCH = os.getenv("ALLOW_WEB_FETCH", "true").lower() == "true"

DEFAULT_ADDRESS = "130 Alex Avenue, Schofields NSW 2762"

st.set_page_config(page_title="PropLens MVP", layout="wide")
st.title("PropLens MVP")
st.caption("Auto-loads a default address, lets you override property facts and finance settings, then computes expenses and cashflow. Polite fetcher that respects robots.txt.")

# Session init
if "_init_done" not in st.session_state:
    st.session_state._init_done = False
if "_last_query_time" not in st.session_state:
    st.session_state._last_query_time = 0.0
if "selected_address" not in st.session_state:
    st.session_state.selected_address = None

with st.sidebar:
    st.header("Property Search")
    query = st.text_input("Enter Australian address", value=DEFAULT_ADDRESS)

    suggestions = []
    if query and len(query) >= 4:
        now = time.time()
        if now - st.session_state._last_query_time > 0.4:
            suggestions = search_addresses(query)
            st.session_state._last_query_time = now

    selected = None
    if suggestions:
        default_idx = 0
        selected = st.selectbox(
            "Suggestions", suggestions, index=default_idx, format_func=lambda a: a.display_name
        )

    run = st.button("Find details", type="primary")

# Auto-run on first load if we have suggestions
if not st.session_state._init_done and suggestions:
    st.session_state._init_done = True
    run = True

col_left, col_right = st.columns([2, 1])

if run and selected:
    with col_left:
        st.subheader("Property details")
        st.write(
            f"**Address:** {selected.display_name}\n\n**Suburb:** {selected.suburb or '-'} | **State:** {selected.state or '-'} | **Postcode:** {selected.postcode or '-'}"
        )

        source_urls: list[str] = []
        facts_jsonld = {}

        if ALLOW_WEB_FETCH:
            urls = find_candidate_urls(selected)
            for u in urls:
                data, allowed, fetched = extract_schema_org(u)
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                if allowed and fetched:
                    source_urls.append(f"{u} [robots: allowed] [ts: {ts}]")
                elif not allowed:
                    source_urls.append(f"{u} [robots: disallowed] [ts: {ts}]")
                else:
                    source_urls.append(f"{u} [robots: allowed, no JSON-LD] [ts: {ts}]")
                if data:
                    facts_jsonld = normalise_jsonld(data)
                    break
        else:
            st.warning("Web fetch disabled by ALLOW_WEB_FETCH flag. Using open data and estimates only.")

        open_parcel = try_open_parcel(selected)
        land_hint = float(open_parcel["land_sqm"]) if open_parcel and open_parcel.get("land_sqm") else None
        est = estimate_from_heuristics(selected, land_hint)

        prop: PropertyFacts = merge_facts(
            address=selected,
            jsonld_map=facts_jsonld,
            open_data=open_parcel,
            estimated_map=est,
            source_urls=source_urls,
        )

        # --- Property Facts Overrides ---
        st.markdown("### Property facts (override any)")
        colA, colB, colC = st.columns(3)
        with colA:
            ov_beds = st.number_input("Beds", 0, 10, int(getattr(prop.beds, "value", 3) or 3))
            ov_baths = st.number_input("Baths", 0, 10, int(getattr(prop.baths, "value", 2) or 2))
        with colB:
            ov_cars = st.number_input("Car spaces", 0, 6, int(getattr(prop.cars, "value", 1) or 1))
            ov_land = st.number_input("Land size (sqm)", 0.0, 5000.0, float(getattr(prop.land_sqm, "value", 0.0) or 0.0), step=1.0)
        with colC:
            ov_build = st.number_input("Build size (sqm)", 0.0, 1000.0, float(getattr(prop.build_sqm, "value", 0.0) or 0.0), step=1.0)
            ov_last_sold = st.number_input("Last sold price (override)", 0.0, 20_000_000.0, float(getattr(getattr(prop, "last_sold_price", None), "value", 0.0) or 0.0), step=10_000.0)

        prop.beds.value = ov_beds
        prop.baths.value = ov_baths
        prop.cars.value = ov_cars
        prop.land_sqm.value = ov_land if ov_land else getattr(prop.land_sqm, "value", None)
        prop.build_sqm.value = ov_build if ov_build else getattr(prop.build_sqm, "value", None)
        if prop.last_sold_price:
            prop.last_sold_price.value = ov_last_sold or prop.last_sold_price.value

        # --- Mortgage Controls ---
        st.markdown("### Expenses and cashflow")
        with st.container(border=True):
            price_input = st.number_input(
                "Purchase price (AUD)",
                min_value=0,
                value=int(float(getattr(prop.last_sold_price or FieldValue(value=0, source='estimated', confidence=0.1), 'value') or 0))
            )

            owner_occ = st.checkbox("Owner occupier", value=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                deposit_pct = st.slider("Deposit percent", 0, 60, 20)
                repayment_type = st.selectbox("Repayment type", ["P&I", "Interest Only"], index=0)
            with col2:
                rate_type = st.selectbox("Rate type", ["Variable", "Fixed"], index=0)
                variable_rate_pct = st.number_input("Variable rate % p.a.", min_value=0.0, value=6.25, step=0.05)
            with col3:
                fixed_rate_pct = st.number_input("Fixed rate % p.a.", min_value=0.0, value=5.85, step=0.05)
                fixed_years = st.slider("Fixed period (years)", 0, 5, 0)

            io_years = st.slider("Interest-only period (years, if IO)", 0, 10, 0)
            years = st.slider("Loan term (years)", 5, 35, 30)

            loan_amount = max(0.0, price_input * (1 - deposit_pct / 100))
            active_rate = pick_active_rate(rate_type, variable_rate_pct, fixed_rate_pct, fixed_years)

            # stamp duty and council
            stamp = calc_stamp_duty(price_input, state=(prop.address.state or "NSW"), owner_occ=owner_occ)
            council = calc_council_rates(prop.address.lga or "Default LGA", land_sqm=float(getattr(prop.land_sqm, 'value', 0) or 0))

            # insurance
            sum_insured = estimate_sum_insured(build_sqm=float(getattr(prop.build_sqm, 'value', 0) or 180.0))
            risk = st.select_slider("Risk band (insurance)", options=["low", "medium", "high"], value="medium")
            premium = premium_from_risk(sum_insured, risk)

            # mortgage repayment
            monthly_repay = calc_repayments(
                loan_amount,
                annual_rate=active_rate,
                years=years,
                repayment_type=("IO" if repayment_type.startswith("Interest") else "P&I"),
                interest_only_years=io_years
            )

            # rent and PM fee
            lga_yield_band = 0.036
            est_rent_week = price_input * lga_yield_band / 52 if price_input > 0 else 550
            rent_week = st.number_input("Weekly rent estimate", min_value=0.0, value=float(round(est_rent_week,2)))
            pm_fee_pct = st.slider("Property manager fee percent", 0.0, 12.0, 6.0, 0.5)

            # monthly cashflow
            outgoings_month = (council/12.0) + (premium/12.0)
            inflow_month = (0 if owner_occ else rent_week * 52 / 12 * (1 - pm_fee_pct/100))
            verdict = calc_cashflow(inflow_month, monthly_repay, outgoings_month)

            st.write(f"**Stamp duty:** ${stamp:,.0f}")
            st.write(f"**Council rates (annual):** ${council:,.0f}")
            st.write(f"**Insurance premium (annual):** ${premium:,.0f} for sum insured ${sum_insured:,.0f}")
            st.write(f"**Monthly repayment:** ${monthly_repay:,.0f}")
            st.write(f"**Net monthly cashflow:** ${verdict:,.0f} {'(positive)' if verdict >= 0 else '(negative)'}")

        with st.expander("Sources and timestamps"):
            if source_urls:
                for u in source_urls:
                    st.write(u)
            else:
                st.caption("No third-party fetches used or all were disallowed.")

        if st.button("Export summary to PDF"):
            path = generate_pdf(prop, stamp, council, premium, monthly_repay)
            with open(path, "rb") as f:
                st.download_button("Download PDF", f, file_name="proplens_summary.pdf", mime="application/pdf")

    with col_right:
        st.subheader("Helpers")
        st.select_slider("Buyer Sentiment", ["Very Low", "Low", "Neutral", "High", "Very High"], value="Neutral")
        st.select_slider("Growth Sentiment", ["Weak", "OK", "Strong"], value="OK")

else:
    st.info("Enter an address on the left. After 4 characters, suggestions will appear.")
