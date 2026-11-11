# ELIXIR Atlas data layer problems

11 November 2026

This report records data-layer problems from user feedback and the `atlas_261111` competency-question evaluation. User reports are attributed separately from observations verified during the evaluation of data release `20261111`.

## User reported problems

The sources are the supplied [hackathon feedback notes](</Users/vlad/Downloads/BH_project_26_notes (3).docx>) and the [Systems Biology Community review](https://docs.google.com/document/d/15PFmmdq-msSKy3LaVbJIhtXCmb1UNxeebcK0qRLA_Sg/edit) linked from those notes. The page references below refer to the supplied Word document.

### Missing person associated with Plant Sciences

The reviewer reports that Pierre Larmande appears under Plant Sciences, but Pedro Barros does not. The cited co-lead elections source and its screenshot include both people under Plant Sciences: Pedro Barros at Universidade Nova de Lisboa in Portugal, and Pierre Larmande at CNRS in France.

Record: `initiative:plant-sciences`. Feedback: page 1, “Why is Pierre listed here … but not Pedro?” Cited source: [co-lead elections](https://elixir-europe.org/communities/co-lead-elections).

### Sparse Community membership

The reviewer reports that very few members are listed per Community and describes the Community-to-member-to-service coverage as limited. The reviewer also notes uncertainty about the availability of membership lists.

Feedback: page 1, the comment about the C2 user story and Community-to-member-to-service traversal.

### Unclear identity of Crops and Forest Plants

The reviewer questions whether the Crops and Forest Plants record is the Plant Sciences Community under another name. The feedback does not establish whether these records represent the same Community.

Record: `initiative:crops-and-forest-plants`. Feedback: page 1, “Is this the plant sciences community renamed?”

### Historical name for the Microbiome Community

The reviewer reports that Marine Metagenomics was renamed to the Microbiome Community, while the referenced Atlas record uses Marine Metagenomics.

Record: `initiative:marine-metagenomics`. Feedback: page 1. Cited source: [Community page](https://elixir-europe.org/communities/marine-metagenomics).

### Focus Group transition to a Community

The reviewer reports inconsistent representation of the Domestic Animals Genome and Phenome Focus Group's transition to a Community. The supplied screenshot of the Focus Group page says it was active from 2024 to 2025 and its activities were integrated into the Community in early 2026. The screenshot of the Focus Group directory dates the transition to March 2026.

Record: `initiative:focus-groups-domestic-animals-genome-phenome`. Feedback: pages 1–2. Cited sources: [Focus Group page](https://elixir-europe.org/focus-groups/domestic-animals-genome-phenome) and [Focus Group directory](https://elixir-europe.org/focus-groups).

### Community category includes groups outside the ELIXIR Communities

The reviewer reports that the Community category includes groups that are not ELIXIR Communities. The feedback does not enumerate all affected records.

Feedback: page 2, referring to the Atlas `kind/community` category.

### Disputed separation of project categories

The reviewer reports that the distinction between a commissioned service and a programme project is unclear, and states that there is no real distinction between them. No specific pair of records is identified in this comment.

Feedback: page 3, the comment about commissioned services and programme projects.

### Unclear provenance of Community to training event relationships

The reviewer sees TeSS data in Atlas but cannot identify how the Community-to-training-event relationship was sourced. No particular event or relationship identifier is supplied.

Feedback: page 1, the TeSS comment.

### Missing Portugal association for Systems Biology

The Systems Biology reviewers report that the Community has nine associated Nodes but does not include ELIXIR Portugal. They report that Miguel Rocha is listed as a co-lead, his Atlas person profile associates him with ELIXIR Portugal, and the official Community page identifies him with ELIXIR Portugal.

Source: the Systems Biology review, “Missing ELIXIR Portugal association in Systems Biology Community.”

### Missing Systems Biology tool collection coverage

The Systems Biology reviewers report that Atlas lists three individual tools but does not reflect the broader collections linked from the Community page. They identify three curated bio.tools domains: constraint-based modelling, logical and qualitative modelling, and rule-based modelling. Each collection contains multiple tools.

Source: the Systems Biology review, “Incomplete representation of tools in the Systems Biology Community.”

### Contact from another Community associated with Systems Biology

The Systems Biology reviewers report that `single-cell-omics-coleads@elixir-europe.org` appears among the Systems Biology contacts, alongside `systems-biology-coleads@elixir-europe.org`. The former is identified in the feedback as belonging to another Community.

Source: the Systems Biology review, “Internal registration links displayed as contacts in the Systems Biology Community,” including its comment about the Single-Cell Omics address.

## Problems observed during the evaluation

These observations concern data release `20261111`. Question numbers refer to the [21-question CQ set](../eval/cqs/atlas_261111). The earlier [trace review findings](../eval/results/cq21-iteration-20261111/build-findings.json) record these three data issues.

### Incomplete group status and mixed Community scope

The stored `initiative.kind = 'community'` category includes both pan-ELIXIR Communities and national groups. The trace review identified four pan-ELIXIR Communities with null status. Across all records, the status query returned the following counts:

| Kind | Current | Completed | Null status |
| --- | ---: | ---: | ---: |
| Community | 17 | 1 | 8 |
| Focus Group | 4 | 9 | 12 |
| Platform | 2 | 0 | 3 |

Affected questions: **001**, Community overlaps; **002**, public activity; **005**, people holding leadership roles in more than two groups.

Evidence: [stored status counts](../eval/results/atlas_261111-v1__skill-api__cq21-baseline__gpt-6-luna/atlas_261111-005__2Sb23vh/artifacts/workspace/evidence/response_005_initiative_status_counts.json).

### Meeting reports without the corresponding Community relationships

The trace review found the following reports in the stored outputs:

| Report | Stored publication date | Relationship observation |
| --- | --- | --- |
| ELIXIR Galaxy Community hybrid meeting report | 2026-08-04 | No `OutputOf` relationship to the Galaxy Community. |
| Single-Cell Omics meeting report | 2026-10-21 | No `OutputOf` relationship to the Single-Cell Omics Community. |
| Hybrid event meeting of ELIXIR Toxicology community | 2026-09-08 | Linked to INTOXICOM, without a link to the Toxicology Community. |

The Galaxy and Single-Cell records have IDs `f1000:data-input-f1000-documents-15-1280-4b5d7a10821a-html` and `f1000:data-input-f1000-documents-15-1758-bc3d1f3883ee-html`, respectively.

Affected questions: **001**, Community overlaps; **002**, public activity.

Evidence: [Community-linked outputs returned in the baseline](../eval/results/atlas_261111-v1__skill-api__cq21-baseline__gpt-6-luna/atlas_261111-002__zMJw6Dn/artifacts/workspace/evidence/005_response.json), [later retrieval by Community name mentions](../eval/results/atlas_261111-v1__skill-api__cq21-improved__gpt-6-luna/atlas_261111-002__Nwy67jM/artifacts/workspace/evidence/28_recent_outputs_name_mentions.json), and the [trace review findings](../eval/results/cq21-iteration-20261111/build-findings.json).

### RDM joining and onboarding conditions absent from extracted evidence

The reviewed RDM SourceStatement preserves the Community email address, the Life Science Login registration URL, and the onboarding document URL. It does not preserve the membership approval requirement or the condition that the onboarding document becomes available after approval. Those conditions appear in the CQ reference material.

Record: `statement:fd62d1d81c0112a3`, extracted from the RDM Community page. Affected questions: **003**, contacts and joining; **004**, reusable onboarding practices.

Evidence: [retrieved SourceStatement with extraction provenance](../eval/results/atlas_261111-v1__skill-api__cq21-baseline__gpt-6-luna/atlas_261111-003__XKE9gJw/artifacts/workspace/evidence/response_011.json), [joining question and reference](../eval/cqs/atlas_261111/questions/atlas_261111-003.yaml), and [onboarding question and reference](../eval/cqs/atlas_261111/questions/atlas_261111-004.yaml).
