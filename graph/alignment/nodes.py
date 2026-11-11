import re
from dataclasses import dataclass

from .names import ascii_fold


@dataclass(frozen=True)
class NodeEntry:
    node_id: str
    name: str
    kind: str
    country: str | None
    aliases: tuple[str, ...]


def member(slug: str, label: str, codes: tuple[str, ...], *brands: str, country: str | None = None) -> NodeEntry:
    names = (f"ELIXIR {label}", label, *(f"ELIXIR-{code}" for code in codes), *(f"ELIXIR {code}" for code in codes))
    return NodeEntry(f"node:{slug}", f"ELIXIR {label}", "member_node", country or label, names + brands)


NODES: tuple[NodeEntry, ...] = (
    member("belgium", "Belgium", ("BE",)),
    member("cyprus", "Cyprus", ("CY",)),
    member("czech-republic", "Czech Republic", ("CZ",), "Czechia", "Czech", "ELIXIR Czechia", "ELIXIR: The Czech Republic Node", country="Czechia"),
    member("denmark", "Denmark", ("DK",)),
    member("estonia", "Estonia", ("EE",)),
    member("finland", "Finland", ("FI",)),
    member("france", "France", ("FR",), "IFB", "French Institute of Bioinformatics", "Institut Français de Bioinformatique"),
    member("germany", "Germany", ("DE",), "de.NBI", "German Network for Bioinformatics Infrastructure"),
    member("greece", "Greece", ("GR", "EL")),
    member("hungary", "Hungary", ("HU",)),
    member("ireland", "Ireland", ("IE",)),
    member("israel", "Israel", ("IL",)),
    member("italy", "Italy", ("IT", "IIB"), "ELIXIR-ITA", "ELIXIR Italy (IIB)"),
    member("luxembourg", "Luxembourg", ("LU",)),
    member("malta", "Malta", ("MT",)),
    member("netherlands", "Netherlands", ("NL",), "The Netherlands", "ELIXIR the Netherlands"),
    member("norway", "Norway", ("NO",)),
    member("portugal", "Portugal", ("PT",), "BioData.pt", "BioData.pt - ELIXIR Portugal"),
    member("slovakia", "Slovakia", ("SK",)),
    member("slovenia", "Slovenia", ("SI",)),
    member("spain", "Spain", ("ES",), "INB", "Spanish National Bioinformatics Institute", "INB/ELIXIR-ES"),
    member("sweden", "Sweden", ("SE",), "NBIS"),
    member("switzerland", "Switzerland", ("CH",)),
    member("uk", "UK", ("UK",), "United Kingdom", "ELIXIR United Kingdom", "ELIXIR-UK Node", country="United Kingdom"),
    NodeEntry("node:embl-ebi", "EMBL-EBI", "embl_ebi", None, ("EMBL-EBI", "ELIXIR EMBL-EBI", "EMBL's European Bioinformatics Institute", "European Bioinformatics Institute")),
    NodeEntry("node:hub", "ELIXIR Hub", "hub", None, ("ELIXIR Hub", "Hub", "ELIXIR Hub (EMBL)", "ELIXIR-Hub")),
)

CODES = {code: entry.node_id for entry in NODES for alias in entry.aliases if (code := alias.removeprefix("ELIXIR-")) != alias and len(code) == 2}


def squash(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", ascii_fold(value).lower()).strip()


ALIASES = {squash(alias): entry.node_id for entry in NODES for alias in entry.aliases}
BY_ID = {entry.node_id: entry for entry in NODES}


def resolve_node(value: str | None) -> str | None:
    if not value:
        return None
    key = squash(value)
    if key in ALIASES:
        return ALIASES[key]
    key = re.sub(r"^(the )?elixir (node )?", "", key).removesuffix(" node").strip()
    return ALIASES.get(key) or ALIASES.get(squash(f"ELIXIR {key}"))


def resolve_code_prefix(value: str) -> str | None:
    match = re.match(r"^([A-Z]{2})-[A-Z]", value.strip())
    return CODES.get(match.group(1)) if match else None
