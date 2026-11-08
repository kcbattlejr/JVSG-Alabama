"""Invented vocabulary for synthetic records. None of it is drawn from source data.

Fictional surnames are chosen to be uncommon and not English words, so name tokens
do not collide with ordinary note vocabulary.
"""

FIRST_NAMES = (
    "Aldric", "Bexley", "Calloway", "Daveth", "Elowen", "Fenwick", "Galen", "Harlow",
    "Isolde", "Jarrell", "Kestrel", "Lenora", "Marisol", "Nevin", "Odalys", "Perrin",
    "Quenby", "Rosalind", "Soren", "Tamsin", "Ulrich", "Verity", "Wystan", "Xiomara",
    "Yarrow", "Zebulon", "Anouk", "Bramwell", "Cosima", "Desmond", "Eulalie", "Florian",
    "Gwynne", "Hollis", "Imogen", "Jethro", "Kalinda", "Leopold", "Mireille", "Nolan",
    "Octavia", "Piers", "Rafferty", "Saoirse", "Thaddeus", "Undine", "Vashti", "Wendeline",
    "Ximena", "Yusuf", "Zinnia", "Ambrose", "Briony", "Cormac", "Delphine", "Evander",
)
LAST_NAMES = (
    "Abernathy-Quill", "Brannagh", "Castellow", "Dunmore", "Ellesworth", "Fairbrook",
    "Galloran", "Hollingsby", "Ironwood", "Jessop", "Kettleby", "Larkspur", "Merriwether",
    "Northcott", "Oakhurst", "Pennywhistle", "Quarrington", "Ravensdale", "Silverthorn",
    "Thistlewood", "Underhay", "Vantongeren", "Wexcombe", "Yardley", "Zabrinski",
    "O'Daire", "McAllaster", "Ashgrove", "Blackwater", "Corrigall", "Drummelow",
    "Eskerby", "Fernsby", "Glenarvon", "Hazelrigg", "Inchbald", "Jardine", "Kilbride",
    "Lowestoft", "Marchbanks", "Netherby", "Ostrander", "Pemberton-Vale", "Quillon",
    "Rookwood", "Sandoval-Reyes", "Tregarthen", "Uffington", "Vellacott", "Wolstenholme",
    "Achterberg", "Bellweather", "Coldbrook", "Delacroix-Hunt", "Everleigh", "Fitzwarren",
)
MIDDLE_PARTICLES = ("Van", "Del")
SUFFIXES = ("Jr", "Sr", "II")

# (last, suffix, first, title) in the MIS "Last, Sfx., First" staff format.
STAFF = (
    ("Quintavalle", "Jr", "Ferris", "DVOP Specialist"),
    ("Marchetti-Oyelaran", "Sr", "Corwin", "Veterans Employment Representative"),
    ("Thornquist", "II", "Lysander", "Workforce Development Specialist"),
)
CASE_MANAGER_NAMES = (("Halvorsen", None, "Brisa"), ("Quintavalle", "Jr", "Ferris"))

THIRD_PARTY_FIRST = ("Rowena", "Caspian", "Marguerite", "Lucan", "Philippa", "Barnaby")
THIRD_PARTY_LAST = ("Penhallow", "Strickmere", "Vandersloot", "Ashcombe", "Kingswell")

STREETS = (
    "Magnolia Bend", "Pecan Hollow", "Live Oak Ridge", "Cypress Landing", "Azalea Crest",
    "Heron Bayou", "Saltmarsh", "Bluff Creek", "Camellia Grove", "Palmetto Run",
)
STREET_TYPES = ("St", "Rd", "Ave", "Dr", "Ln", "Ct", "Blvd", "Street", "Road", "Drive")
UNITS = ("Apt 4B", "Unit 12", "Lot 7", "Apt 210", "Suite 300")
OFFICE_ADDRESS = ("515 Commerce Plaza Blvd", "Suite 300")

EMPLOYERS = (
    "Gulfport Marine Fabrication", "Bayline Logistics", "Southpoint Medical Group",
    "Crescent Utility Services", "Harborview Hospitality", "Delta Steel Works",
    "Pinebelt Aerospace", "Coastal Freight Partners", "Riverbend Manufacturing",
)
TRAINING_PROVIDERS = (
    "Coastal Technical Institute", "Bayside Community College",
    "Gulf Region CDL Academy", "Southern Welding Center",
)
REFERRAL_AGENCIES = (
    ("HUD-VASH", "HSG"), ("VA Medical Center", "MED"), ("Vet Center", "MED"),
    ("Legal Services clinic", "LEG"), ("Transit voucher program", "TRN"),
    ("Supportive Services for Veteran Families", "HSG"), ("county probation office", "LEG"),
)
OCCUPATIONS = (
    "welder", "CDL driver", "warehouse associate", "maintenance technician",
    "security officer", "electrician helper", "forklift operator", "medical records clerk",
)
