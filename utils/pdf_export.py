import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from models.facts import PropertyFacts


def generate_pdf(prop: PropertyFacts, stamp_duty: float, council: float, premium: float, monthly_repay: float) -> str:
    path = os.path.abspath("proplens_summary.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "PropLens Summary")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Address: {prop.address.display_name}")
    y -= 15
    c.drawString(40, y, f"Suburb: {prop.address.suburb or '-'}  State: {prop.address.state or '-'}  Postcode: {prop.address.postcode or '-'}")
    y -= 25

    def line(label, value):
        nonlocal y
        c.drawString(40, y, f"{label}: {value}")
        y -= 15

    line("Dwelling type", str(getattr(prop.dwelling_type, 'value', None)))
    line("Beds", str(getattr(prop.beds, 'value', None)))
    line("Baths", str(getattr(prop.baths, 'value', None)))
    line("Car spaces", str(getattr(prop.cars, 'value', None)))
    line("Land sqm", str(getattr(prop.land_sqm, 'value', None)))
    line("Build sqm", str(getattr(prop.build_sqm, 'value', None)))

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Costs")
    y -= 20
    c.setFont("Helvetica", 10)
    line("Stamp duty", f"${stamp_duty:,.0f}")
    line("Council (annual)", f"${council:,.0f}")
    line("Insurance (annual)", f"${premium:,.0f}")
    line("Monthly repayment", f"${monthly_repay:,.0f}")

    y -= 20
    c.setFont("Helvetica", 8)
    c.drawString(40, y, "Indicative only. Data may be estimated. Third-party pages fetched only if robots allowed.")

    c.showPage()
    c.save()
    return path