from __future__ import annotations

# (name, category, jurisdiction, url, notes)
PUBLIC_RECORD_SOURCES: list[tuple[str, str, str, str, str]] = [
    ("SEC EDGAR Full Text", "sec", "US", "https://www.sec.gov/edgar/search/", "Issuer filings, exhibits, signatures, related-party disclosures."),
    ("OTC Markets Symbol Search", "otc", "US", "https://www.otcmarkets.com/search", "OTC issuer profile, disclosures, transfer-agent clues."),
    ("Nevada SOS Business Search", "business", "NV", "https://www.nvsos.gov/businesses", "Entity/officer/registered-agent search."),
    ("Nevada UCC Search", "ucc", "NV", "https://www.nvsos.gov/sos/businesses/ucc-filings", "Debtor/secured-party lender clues."),
    ("Clark County Assessor", "property", "NV", "https://www.clarkcountynv.gov/government/assessor/property_search/real_property_records.php", "Real property ownership/address clues."),
    ("California Bizfile", "business", "CA", "https://bizfileonline.sos.ca.gov/search", "CA business/foreign entity search."),
    ("Los Angeles County Assessor", "property", "CA", "https://portal.assessor.lacounty.gov/", "LA property search."),
    ("Orange County Assessor", "property", "CA", "https://ocassessor.gov/", "OC property search."),
    ("Arizona Corporation Commission", "business", "AZ", "https://ecorp.azcc.gov/EntitySearch/Index", "AZ entity/officer search."),
    ("Maricopa County Assessor", "property", "AZ", "https://mcassessor.maricopa.gov/", "Phoenix-area property search."),
    ("PACER", "court", "US", "https://pacer.uscourts.gov/", "Federal litigation/bankruptcy search."),
    ("CourtListener / RECAP", "court", "US", "https://www.courtlistener.com/", "Free federal docket search; party names and filings."),
    ("NETR Online Public Records", "property", "US", "https://publicrecords.netronline.com/", "State/county assessor and recorder portal directory."),
    ("Black Book Online Property", "property", "US", "https://www.blackbookonline.info/Property.aspx", "Property record search index by state."),
    ("National Center for State Courts", "court", "US", "https://www.ncsc.org/information-and-resources/state-court-websites", "Directory of state court record portals."),
    ("BRB Public Records", "directory", "US", "https://www.brbpub.com/", "State/county public record portal directory."),
    ("NARA Genealogy / Records", "records", "US", "https://www.archives.gov/research/genealogy", "Federal records index; historical address clues."),
    ("USPS ZIP Lookup", "address", "US", "https://tools.usps.com/zip-code-lookup.htm", "Validate city/state/ZIP combinations."),
]
