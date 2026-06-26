from __future__ import annotations

# Free / freemium people-finder portals for manual lookup. Verify identity before service.
PEOPLE_SEARCH_SOURCES: list[tuple[str, str, str, str, str]] = [
    ("TruePeopleSearch", "people-search", "US", "https://www.truepeoplesearch.com/", "Free name/phone/address lookup; strong for recent US residences."),
    ("FastPeopleSearch", "people-search", "US", "https://www.fastpeoplesearch.com/", "Free aggregator; cross-check hits with assessor/court records."),
    ("That's Them", "people-search", "US", "https://thatsthem.com/", "Free people search; email/phone hints."),
    ("SearchPeopleFree", "people-search", "US", "https://www.searchpeoplefree.com/", "Free name search with relatives/associates."),
    ("FamilyTreeNow", "people-search", "US", "https://www.familytreenow.com/", "Free genealogy-style people finder; relative graph."),
    ("CyberBackgroundChecks", "people-search", "US", "https://www.cyberbackgroundchecks.com/", "Free people search; verify against primary records."),
    ("USPhoneBook", "people-search", "US", "https://www.usphonebook.com/", "Reverse phone and name lookup."),
    ("ZabaSearch", "people-search", "US", "https://www.zabasearch.com/", "Legacy free people search; use as a lead only."),
    ("AnyWho", "people-search", "US", "https://www.anywho.com/", "White/Yellow pages style directory."),
    ("Whitepages", "people-search", "US", "https://www.whitepages.com/", "Directory; limited free preview."),
    ("Spokeo", "people-search", "US", "https://www.spokeo.com/", "Aggregator; freemium — use only if lawfully licensed."),
    ("BeenVerified", "people-search", "US", "https://www.beenverified.com/", "Paid aggregator; licensed-skip-trace workflows only."),
    ("Intelius", "people-search", "US", "https://www.intelius.com/", "Paid aggregator; licensed workflows only."),
    ("Radaris", "people-search", "US", "https://radaris.com/", "People search; freemium."),
    ("PeekYou", "people-search", "US", "https://www.peekyou.com/", "Social/web footprint index."),
    ("Nuwber", "people-search", "US", "https://nuwber.com/", "People search aggregator."),
    ("ClustrMaps", "people-search", "US", "https://clustrmaps.com/", "Neighbor/resident clustering around an address."),
    ("VoterRecords.com", "voter", "US", "https://voterrecords.com/", "State voter registration where publicly available."),
    ("OpenCorporates", "business", "US", "https://opencorporates.com/", "Officer/registered-agent ties for individuals with businesses."),
    ("LinkedIn People", "social", "US", "https://www.linkedin.com/search/results/people/", "Employment/location hints; manual review only."),
    ("Facebook People Search", "social", "US", "https://www.facebook.com/search/people/", "Social graph hints; manual review only."),
]
