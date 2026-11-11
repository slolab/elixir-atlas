# atlas_261111 sidenotes

How the reference answers were derived, data-quality notes and details left out of the answers. Judges and annotators do not see this file.


How the reference answers for 001 to 005 were derived, data-quality notes and details left out. Judges and annotators do not see this file.

## 001: overlapping Communities

- Current Communities: the 19 on https://elixir-europe.org/communities (crawled 4 November 2026). The page lists Marine Metagenomics as former; it became Microbiome.
- Projects: 238 unique Scientific Programme and Commissioned Service pages carry a "Platform/Community" field. 15 list two or more current Communities and end in 2025 or later. Two of those are area-level pages (Cellular and molecular research: 13 Communities; Human data and translational research: 5 Communities), left out as clusters because they are programme areas, not projects.
- Older overlapping projects (left out): Proteomics pipelines with Metabolomics (2019–21), CATH/SWISS-MODEL with Federated Human Data and 3D-BioInfo (2018–20), Data validation with Plant Sciences, Galaxy and Metabolomics (2018–19), ELIXIR integration from a user perspective (2017).
- The nine Biodiversity, food security and pathogens projects (FAIRyMAGs, Odyssey, E-PAN, HARVEST, KYBELE, FAIRferm, BioDiv-FAIR-Checker, FAIR non-human pathogen standards, plant FAIR assistant) have an empty Community field, so they give no overlap evidence. The Microbiome page lists FAIRyMAGs and Odyssey as its Commissioned Services.
- bio.tools: 34,819 records after deduplication by biotoolsID. Only 12 Community values are used: 3D-BioInfo 83, Plant Sciences 29, Galaxy 25, Metabolomics 25, Rare Diseases 20, Proteomics 18, Marine Metagenomics 13, Federated Human Data 11, Microbial Biotechnology 8, IDP 5, hCNV 5, Systems Biology 3. Biodiversity, Cancer Data, Domestic Animals, Food and Nutrition, Microbiome, RDM, Single-Cell Omics and Toxicology have no tag. omnipy (9 Communities) and Galaxy France (6) inflate pair counts and were ignored. Other multi-tag tools: JASPAR, CHOPCHOP, immuneML, DSW at IFB, FANTASIA, galaxy.sciensano.be, SKM.
- Zenodo has no per-Community Zenodo community; only two records name two Communities in title or description (ELIXIR-STEERS M2.5, a 2022 BioData.pt poster). Not used for 001.
- F1000 article 14-884 Table 1 lists each Community's external partners. Shared partners besides Beacon and Bioschemas: GA4GH (Federated Human Data, Galaxy, hCNV, Rare Diseases), BGE (Biodiversity, Galaxy), GDI (Federated Human Data, Galaxy), BBMRI-ERIC (Federated Human Data, Rare Diseases), HUPO-PSI (IDP, Proteomics), ELIXIR-CONVERGE (Federated Human Data, RDM).
- Community pages also cross-reference each other: Microbiome names the Biodiversity Community as its closest partner; Galaxy names Workflow4Metabolomics and GalaxyP for Metabolomics; Rare Diseases points to the Federated Human Data page for EGA access; Plant Sciences points to Galaxy workflows.
- Use case question A6 (similar events or outputs planned this year) is not covered; the events listing gives titles and dates only.

## 002: Communities without recent public activity

- Window: 11 November 2025 to the crawl (4 November 2026). Upcoming events on the events listing (Food and Nutrition 24 Nov 2026, 3D-BioInfo 25 Nov 2026, Microbiome 16 Feb 2027, Plant Sciences 17 Feb 2027) were counted as current evidence because the announcement is current.
- Sources searched: Related news on each Community page; the ELIXIR events listing and the 103 event pages; 733 F1000 items (titles, abstracts and page text before references); 419 Zenodo records from 11 November 2025 on; TeSS events and materials (latest Community-named TeSS items: FHD Community Day Nov 2024, IDP meeting May 2024, hCNV webinar May 2024); Node websites with a publication date in the window.
- Cancer Data: the FAIR-FEGA, federated learning and "Empowering users" pages were all published 30 June 2025 and modified in 2026; page edits were not counted. Spatial2Galaxy lists Cancer Data, and its F1000 reports (15-992, 15-1249, 15-1507, 15-1508, 15-1577 to 15-1579, June to September 2026) do not name any Community. The INB poster (June 2026) and the co-lead election list (candidate Lifang Liu) mention the Community but are not its activity. CANDLE (2025–2028) is an EU project on cancer data nodes; its page does not name the Community.
- Microbial Biotechnology: the latest items naming the Community itself are ELIXIR-UK pages (2024) and the 2022 Systems Biology F1000 article. DBTLHub (January 2024 to December 2026) lists it; no DBTLHub output was found in the data.
- Proteomics: the F1000 article 14-884 (9 September 2025) describes its SDRF work. The RCI-M workshop report (7 March 2026) mentions proteomics but not the Proteomics Community.
- Federated Human Data: the ELIXIR-UK "Human Data Community" call of 21 January 2026 belongs to ELIXIR-UK's national community, not to the ELIXIR Community. EGA posters from June 2026 do not name the Community.
- ELIXIR-STEERS M2.5 says its events had "coverage from" seven Communities. It is unclear whether that means attendance or topic coverage. It is the only window item for FHD and IDP.
- The ELIXIR Annual Report 2025 (F1000 15-1050) was not mined; it may record November and December 2025 Community activity.
- Page "dateModified" values (useful as weak signals, not counted): Metabolomics 10 Jan 2025, Microbial Biotechnology 9 Jan 2025, Proteomics 27 Jan 2025, Plant Sciences 25 Mar 2025, Cancer Data 11 Aug 2025, IDP 22 Sep 2025.

## 003: RDM contact, channel and joining

- The Community page gives rdm@elixir-europe.org for both the mailing list and the co-leads. The Handbook says each Community has a separate co-lead mailing list; for RDM no separate co-lead address appears anywhere in the data.
- Katharina Heil's email comes from the Hub Communities Team block on the Communities page, not from the RDM page.
- The Join link goes to the Life Science Login registrar with group "Community:User Communities:Research Data Management".
- The Handbook's join guides for ELIXIR and non-ELIXIR members are Google Drive links and are not in the data.
- The question changes the use case's "I am a member" to "I want to take part", because a member would not ask how to join.

## 004: onboarding

- "onboarding" was searched across all of data/input. Community-related hits: the RDM page, the DATAREX end report record, the co-lead elections page. Other hits are Node onboarding (PeoplePulse, ELITMa Luxembourg example), Training Coordinator onboarding (Training Platform M3.10, M3.11, M3.12), FEGA onboarding, Snakemake onboarding and e-learning onboarding in Nodes.
- The RDM onboarding document (https://elixir-europe.org/documents/elixir-rdm-community-onboarding) was not crawled. The DATAREX end report PDF was not crawled either; only its Zenodo record.
- The Training Platform page plans "an onboarding process for" Training Platform members under WP3.
- The Demystifying ELIXIR webinar is aimed at people new to ELIXIR and those onboarding them in Nodes. Not listed because it is an event, not reusable onboarding material.
- The elections page links a "Community co-lead election process document" (not crawled) that may describe the handover.

## 005: people in several groups

- Re-derived from the leadership blocks of the 19 Communities, 5 Platforms and 6 current Focus Groups, plus Platform work-package "Leads" lines. Same five people above two groups as atlas_261110-001; the counts are unchanged.
- Changes since atlas_261110: new Platform leads in 2026 (Teresa D'Altri, Data; Vassilios Ioannidis, Interoperability; Matúš Kalaš, Tools; Geert van Geest, Training), each in one group because their WP roles are in the same Platform. Hub staff Daniel Barrowdale (Cancer Data, hCNV), Magda Chegkazi (FHD, Rare Diseases), Jonathan Tedds (Compute, Tools) and Fabio Liberante (Data, Interoperability) each hold two. The Domestic Animals Focus Group became a Community in March 2026.
- The time-commitment half of the archived question was dropped: it belongs to use case A7, which is out of scope this week.
- The Data Platform page still lists "SE-UU - Mihail Anton 1.5" among the WP3 leads, a planning leftover. Counted, Anton has five groups.
- Science tier leadership (not counted): Biodiversity, food security and pathogens (Tereza Manousaki, Cyril Pommier, Robert Waterhouse, Katharina Heil, Physilia Chua); Cellular and molecular research (Patrick Aloy, Fotis Psomopoulos, Silvio Tosatto); Human data and translational research (Sergi Beltran, Macha Nikolski, Dylan Spalding, Andrew Stubbs, Serena Scollen, Magda Chegkazi). With these, Tosatto, Psomopoulos and Chegkazi reach three.
- The Microbiome page shows the label "Deputy Training Coordinator" next to Bérénice Batut. It looks like a profile field (likely her Node Training Coordinator role), not a Training Platform leadership role, and was not counted.
- Name matching: "Anton" also matches Antonio Rausell (hCNV), Juan Antonio Vizcaíno (Proteomics) and Antonio Hermoso Pulido (Interoperability WP4). Hervé Ménager, Björn Grüning and Matúš Kalaš appear on the Galaxy page only in a 2017 publication. Lennart Martens (Proteomics) and Marvin Martens (Toxicology support) are different people.


## 006: ELIXIR Estonia's projects

- Derived by finding every elixir-europe.org project page whose "Nodes involved" list contains "ELIXIR Estonia" (internal-projects/commissioned-services, about-us/commissioned-services, how-we-work/scientific-programme, internal-projects/staff-exchange-programme), plus the three CORDIS fact sheets. The Commissioned Services list pages do not show Nodes, so pages missing from the crawl would be missing from the answer.
- Two older pages duplicate two of the services under /about-us/commissioned-services/ (elixir-integration-user-perspective, fluxomics-workflows). Each counts once.
- No Scientific Programme 2024-28 page other than Node support, and no Implementation Study under /about-us/implementation-studies/, lists Estonia.
- The 2024-26 Platform pages give "January 2024 to January 2026"; the Compute, Tools and Training work plans run M01 to M36 and are titled 2024-2026. Tools Platform milestone reports were still published in November 2026 (M5.1 updated), which supports the 36-month reading.
- Estonian people on the earlier services: Hedi Peterson (integration from a user perspective, data stewardship, Federated Human Data 2019-21, capacity building in interoperability, Tools Platform Ecosystem, 2022-23 bio.tools/EDAM, TeSS and TeSS quality); Kairi Koort (metabolite identification, fluxomics); Ulvi Gerst Talas (2022-23 Beacon infrastructure and Federated EGA; the FEGA metadata report places Ulvi Talas at UT). The ML standards (2023-24), Data Carpentry, learning paths and DATAREX pages name no Estonian person; the DATAREX end report names Heleri Inno and Diana Pilvar and a face-to-face event in Tartu.
- The 2022-fhd page lists Estonia under Nodes involved; the older 2019-21 Federated Human Data page also lists Estonia.
- EXCELERATE D1.4 gives UTARTU 43 person-months in WP1 (tools interoperability and service registry). Not used in the answer.

## 007: ELIXIR Estonia's commitments in ELIXIR-STEERS

- Picked STEERS over the Tools Platform 2024-26 plan. STEERS has four tasks with Tartu, five dated outputs, and three milestone reports that name Estonian people. The Tools plan has one activity co-lead (WP2 Activity 3 Outreach, with deliverables D2.3 at M24 and D2.4 at M36, both led by NL-Leiden).
- The website "Leadership" lists are long contributor lists, not task leads. The D1.6 Task Leaders table (Table 14) has no Tartu name. The deliverable lead table has no Tartu name.
- Task to output mapping: Task 4.1 to D4.2 ("an almanack" in the task text); Task 4.2 to D4.3 (named in the Task 4.1 text) and M4.1 (ELITMa expansion); Task 4.3 to D4.1 (named in the task text). M3.4 "builds primarily on ... Task 3.3 and ... Task 3.4". M3.5 is led by UFR, whose people lead Task 3.4. D3.2 (Report on Community-led efforts to identify critical components across workflows, January 2027) may also draw on Task 3.4; the link is not stated, so it was left out.
- D4.1 was due 31/01/2026 and delivered 05/03/2026. The website deliverables page gives only the month.
- The D1.6 handbook says the grant agreement and annexes, including the estimated budget, are on the STEERS Google Shared Drive, which is internal.
- The 2023 Annual Report says ELIXIR Estonia "participated in the successful bid" for STEERS and appointed Kairi Koort (Tallinn University) as Deputy Head of Node.

## 008: people in current projects

- Scope named in the question to avoid the Platform end-date conflict: STEERS, the three 2024-26 Platform work plans and Node support. DATAREX ended in December 2025 and is out of scope.
- Hedi Peterson is on the Tools CS page and the Node support page. The Compute CS page lists Estonia but names no people; Kaur Alasoo comes from the Compute work plan. The Training CS page names no people.
- Diana Pilvar is not in the Training Platform work plan. She appears as an author of D2.7 (Zenodo, October 2025; version history January 2025) and as a reviewer of Training Platform D4.1 (March 2026).
- Marilin Moor is listed on the 2025 bioinformatics-stats staff exchange; her affiliation is not given, and the exchange is out of scope.
- Kairi Koort's other recent activity (co-author of the 2025 All Hands microbial data workshop report, affiliated to Tallinn University and ELIXIR Estonia) is not a project role.

## 009: STEERS funding for the University of Tartu

- CORDIS fact sheet: net EU contribution €67,500; the organisation's total cost €84,375 appears after the address block, as for every participant on that page. The extracted cordis_participants.jsonl agrees.
- 67,500 / 84,375 = 0.80. The project as a whole is also 80% funded (€3,200,000 of €4,000,000.01).
- The D1.6 handbook mentions in-kind contributions only in general guidance for third parties; it says nothing about Tartu.
- The 2024-28 financial plan lists Estonia's ELIXIR membership contribution (about €10,000 to €14,000 per year). This is not STEERS funding.

## 010: overlap for STEERS Task 4.3

- Chose Task 4.3 because the Training Platform plan cites it by name and an Estonian person sits on each side (Hedi Peterson in the STEERS task list, Priit Adler in Training Platform WP4).
- The Training Platform plan mentions STEERS WP4 ten times (overview, WP3 Activity 1 and 2, WP3.2, WP4 objectives and description).
- Other candidates left out: CONVERGE (ELITMa was developed there; relates to Task 4.2), the ELITMa Module 2 staff exchange (Task 4.2, Module 2 held in Tartu 19-21 May 2025), and the 2022-23 TeSS quality and impact service (training metrics, ended).


## 011: Compute Platform webpage fields

- Two ELIXIR pages describe the same service. The current one, "ELIXIR Compute Platform (2024-TECHNOLOGY-Compute)" under /how-we-work/scientific-programme/technology/24-compute, was published 12 November 2025 and edited 13 October 2026. The older "ELIXIR Compute Platform (2024-26)" under /internal-projects/commissioned-services/2024-compute was published 2 May 2024 and edited 5 June 2026. The older page has the January 2026 end and 13 Nodes.
- Plan partner table (Table 1): leads CZ-MUNI, DE-BIH/Charité, FI-CSC. Members BE-VIB, CH-SIB, CZ-CESNET, DE-FZJ, DE-DKFZ, DE-Giessen, EE-UTARTU, ELIXIR Hub, EMBL-EBI, FR-CNRS, FR-INRAE, GR-ATHENA, IT-INFN/CNR, LU-LNDS, LU-UNILU, NL-Erasmus MC, NL-Health-RI, NL-SURF, UK-UNIMAN (Stian Soiland-Reyes, WP5 member), and AU BioCommons.
- WP5's lead-partner line says DE-FZJ while the named lead is "DE-FUB - Michael R. Crusoe". The answer keeps the person's label.
- Tristan Perard is on the project page only. Two F1000 posters from June 2026 place him at CSC, Finland.
- The ELIXIR-UK site lists the Compute Platform as a UK project. That conflict is used in 014, not here.
- Left out: the deliverable table (D1.1 to D5.x), and the 2025 Face-to-Face report (https://zenodo.org/records/15224009, held in Munich and co-hosted by ELIXIR-DE).

## 012: FAIR-FEGA outputs and date changes

- Re-derived from the archived CQ atlas_261110-008, narrowed to outputs and dates. The page's JSON-LD gives published 30 June 2025 and modified 4 June 2026. The copy at /commissioned-services/science/hdtr/fair-fega is identical.
- The Annual Report 2025 PDF metadata gives creation 4 June 2026 and modification 26 June 2026. The text says the five HDTR projects launched in 2025 are "Scheduled to run through 2026".
- I searched the Zenodo catalogue, F1000 items and all data/input text for "FAIR-FEGA". Only the June 2025 poster (keyword) mentions it, and that poster predates the page. The FEGA Metadata Technical Report cites the poster (doi 10.7490/f1000research.1120212.1) but never names FAIR-FEGA. Its grants are HEREDITARY (101137074) and ELIXIR (211601).
- The FEGA white paper's Zenodo record says v1.1, while the PDF footer says v1.0 (October 2026). It credits EXCELERATE, CONVERGE, CINECA, B1MG, GDI and NordForsk.
- Left out: the BioData.pt news of 9 June 2026 naming Ana Teresa Freitas, Jorge Oliveira and Jorge Silva. It concerns people, not outputs or dates. Also left out: "Advancing FEGA Portugal" (F1000 poster, 22 June 2025), which predates the page.

## 013: ELIXIR Germany in 2026

- Scope: Commissioned Services whose ELIXIR page lists "ELIXIR Germany", plus the three ELIXIR EU grants in CORDIS. Outputs are Zenodo records with a publication date from 1 January to 11 November 2026 and at least one creator with a German affiliation. Records from data/extracted/catalogues/zenodo_records.jsonl were checked against the JSON in data/input.
- BFSP work-package numbers come from the BFSP 2024-2026 Work Plan v2 (zenodo 19469586): WP2 E-PAN, WP3 FAIRyMAGs, WP4 HARVEST, WP7 non-human pathogen metadata, WP8 FAIR plant virtual assistant.
- DATAREX outputs: D3.3 (record 17979335) names project ID 2023-COMM-DATAREX. D2.4 is record 18454311, whose PDF file is "D2.4-DATAREX-End-Report-on-Published-LP-in-TeSS.pdf". The RDM Maturity Model JSON (18172336; Jeanne Wilbrandt, FLI) is probably DATAREX D3.2 but is not labelled, so it was left out.
- Several outputs post-date the pages' end dates. E-PAN ends May 2026 on its page, but D2.5 and D2.6 are dated 17 September. FAIRyMAGs and HARVEST end June 2026, but records are dated September and October. The ELIXIR-UK site gives E-PAN January 2024 to January 2027.
- Affiliation gaps: some German people have empty affiliations on some records (Harald Wagener on the AI Strategy; Daniel Wibberg on the February 2026 microbial data workshop report). Neither record is a Commissioned Service output.
- The BFSP plan lists a German in-kind activity in WP8 (FAIR plant assistant): Activity 4, "Connecting the Dots - Data Gathering (in kind)", with members Sebastian Beier, Daniel Arend and Manuel Feser (DE), months 25 to 36. No output yet.
- The older Training Platform page (2024-26) lists Germany. The 2024–28 Training page does not. The older Platform pages list far more Nodes than the current ones, so "German-listed" depends on which page is used.
- In CONVERGE, the German beneficiaries were HITS, Freiburg, DKFZ and Tübingen. EXCELERATE had no German beneficiary. Both projects ended before 2026.
- The de.NBI page "Commissioned Services of ELIXIR Germany" lists projects from 2017 to 2023 with German PIs. It has no 2024–28 projects.
- STEERS handbook v3 (31 January 2026) names the German Heads of Node as Oliver Kohlbacher and Alexander Sczyrba, with Irena Maus as deputy. Freiburg's total cost in STEERS is €108,250.
- Left out: F1000 posters and articles from 2026, TeSS events and training, bio.tools entries.

## 014: ELIXIR-UK portfolio

- The 2024–28 set is the 33 project pages under /how-we-work/scientific-programme/ (5 Platforms, Infrastructure Services, Node support, 3 People-tier projects, BFSP, CMR and HDTR umbrellas, 9 BFSP, 7 CMR and 5 HDTR projects). UK status comes from each page's "Nodes involved". The CMR overview page was not in the crawl. The CMR projects found are DBTLHub, RCI-M, ontologies of disordered proteins, Spatial2Galaxy, FRET-IDP, PDBe-KB workflows and TELLME.
- I re-parsed the CORDIS amounts from the raw pages. The extraction drops third parties, but no UK or German third parties exist in these three projects. EXCELERATE: 53 participants, 5 UK. CONVERGE: 58 participants, 3 UK. STEERS: 35 participants, with Manchester and Earlham as both beneficiaries and ended partners. UK totals: EXCELERATE €1,375,586; CONVERGE €292,115; STEERS €137,808.
- The ELIXIR-UK projects page lists current projects (BioFAIR Methods Commons, E-PAN, FAIR-in-action bridge, the Interoperability, Tools, Data and Compute Commissioned Services, AgroServ) and 64 completed ones. It labels E-PAN and ELIXIR-CONVERGE "Leading". It gives whole-project budgets for EU projects (for example CONVERGE €9,800,000, AgroServ €14,252,873) and UK amounts for national projects (BioFAIR Methods Commons £4,000,000, July 2026 to July 2028; FAIR-in-action bridge £94,916; DaSH £687,857).
- The UK site's E-PAN page says Rothamsted (Keywan Hassani-Pak) leads E-PAN's work on connecting and sharing pan-genome information. E-PAN itself is led by ELIXIR Belgium (VIB).
- Pre-2024 Commissioned Services with UK involvement (48 ELIXIR projects ending before 2024 on the UK site, more on elixir-europe.org) were left out of the question's scope to keep the answer checkable.
- "In-kind" appears in public data only for other Nodes. FEGA-Connect names the Polish FEGA node as in-kind, and the BFSP plan has a German in-kind activity in WP8. Nothing states the UK's in-kind status.

## 015: tools, standards and best practices for genome-scale metabolic modelling

- "Officially recommended" means named on the Systems Biology Community page, in its white paper (F1000Research 11:1265, v1 7 Nov 2022, v2 31 May 2024) or in "Making Models That Matter" (arXiv 2609.13127, submitted 11 Sep 2026). "Community-supported" means the bio.tools record carries an ELIXIR Community, Node or Platform tag and no Community document recommends the tool.
- bio.tools records were filtered from data/extracted/catalogues/biotools.jsonl and checked against data/input/biotools. 199 records match GEM-related terms in name or description; only CarveMe carries an ELIXIR Community tag. Node-tagged GEM tools without a recommendation: COBRA Toolbox (Luxembourg), merlin (Portugal). Metabolic Atlas (Sweden), MetaNetX (Switzerland) and BioModels (EMBL) are both recommended and Node-tagged.
- MEMOTE's bio.tools record has no ELIXIR tag, only the PerMedCoE collection. standard-GEM and FROG have no bio.tools record.
- No FAIRsharing or RDMkit content was scraped. The COMBINE FAIRsharing link comes from the preprint. The RDMkit systems biology page is a follow-up action in the 2026 meeting report.
- Left out: the Microbial Biotechnology page's planned "evaluation suite for metabolic models" (a goal, not a tool) and the bio.tools collection "Metabolic network modelling" (2 records).

## 016: white papers and recommendations

- The Community page's "Find out more" lists standard-GEM, the PBPK reproducibility paper and the BioHackathon training preprint. Only standard-GEM is GEM-specific.
- The Microbial Biotechnology page links no white paper. The 2018 implementation study report (F1000 documents 7-1369) belongs to "A microbial metabolism resource for Systems Biology", which the project page files under the Data Platform and Microbial Biotechnology. The project page gives July 2016 – February 2017; the Microbial Biotechnology page gives January 2017 – June 2018.
- The Metabolomics fluxomics study (2021) uses Rhea for model reconstruction. It is mentioned in 018, not here, because no report is in the data.
- The bioRxiv, PBPK and BioHackrXiv PDFs are not in the data; only their links on the Community page are.

## 017: TeSS training

- TeSS events (10,323) and materials (3,677) from the extracted catalogues, deduplicated by id. Collection 51 is the Systems Biology Community collection (26 events, 6 materials, matching the TeSS collections facet).
- Upcoming means start date on or after 2026-11-11. Searched titles, descriptions and keywords for genome-scale, constraint-based, flux balance, FBA, COBRA, CNApy and related terms. Only two events match; both are in collection 51.
- Other collection events from 11 Nov 2026: Dynamic Modeling in Systems Biology (Wageningen, 7–11 Dec 2026), multi-omics integration (EMBL-EBI, 8–12 Mar 2027), infectious disease modelling (EMBL-EBI, 11–15 Oct 2027).
- TeSS URLs come from each record's links.self in the raw JSON.
- The material "Systems Biology Implementation Study" (TeSS 5553) is a 2018 recording on microbial metabolism. It is not in collection 51 and was left out as background.

## 018: Communities and contacts

- The Systems Biology page shows "systems-biology-coleads@elixir-europe.org" as link text, but the mailto target is single-cell-omics-coleads@elixir-europe.org. The meeting report lists the systems-biology address as the contact. The old URL /focus-groups/systems-biology serves the same page.
- The 2026 co-lead election lists one open Systems Biology position with John Hancock (University of Ljubljana) "reapplying". The Community page does not list him as co-lead; he gave the "First Four Years" talk at the 2026 meeting. Microbial Biotechnology also has one open position and no listed candidate. Voting closed on 9 Nov 2026; results are due in early December 2026.
- No other Community page mentions genome-scale or constraint-based modelling.

## 019: members and tools

- People were collected from the Community page leadership, the SYBEL page (17 people), the 2026 meeting report (speakers, authors) and the 26 authors of "Making Models That Matter". Exact, accent-insensitive name matching against bio.tools credit_names.
- Matches left out because they are not modelling tools or the link is weak: Silvio Tosatto (APICURON, PASTA, LOBO, ALIGN), Henning Hermjakob (IntAct App, ReactomeGSA, iProX, Enzyme Portal), Ana Conesa (several transcriptomics tools), Marco Pagni (Dotlet, MyHits), Maria Klapa (PICKLE, metabolite database), Miguel Rocha (WebSpecmine, MOSCA, ViralFP), Kristina Gruden (quantGenius, GoMapMan, pISA-tree, Biomine Explorer), Chris Evelo (PSnpBind), Dagmar Waltemath (CovidGraph), Gavin Farrell (DOME Registry), Aristotelis Chatziioannou (ANASTASIA, BioTranslator), Maria Suarez Diez (GBOL), Frank Bergmann (Online SBML Validator, which could be added).
- BioModels credits "Rahuman S Malik-Sheriff"; the preprint writes "Rahuman Sheriff". Treated as one person.
- GlyCombo and GlyComboCLI are glycomics tools. Their tag looks like a curation error, but the record says what it says.

## 020: Communities to bring in

- Evidence per Community: Microbial Biotechnology (DBTLHub, shared co-lead, bundle pilot, white paper section), Plant Sciences (SKM double tag, Gruden, bundle pilot, white paper), Food and Nutrition (bundle outreach, RCI-M, its white paper's nutritional systems biology table and mention of the Systems Biology Focus Group), Toxicology (PBPK paper, RCI-M, Toxicology meeting report, Sara Morsy), Rare Diseases (2023 bundle).
- The white paper itself lists Galaxy (technology), Metabolomics, Microbial Biotechnology, Plant Sciences, Biodiversity, Microbiome, Food and Nutrition, Toxicology, and the human data Communities. Galaxy and Biodiversity were left out as weaker.
- The Toxicology report footer reads "Last updated [08/2025]" and the meeting date is "25–26 June" with no year; F1000 dates the document 8 Sep 2026. The year of the meeting is uncertain.
- Chris Evelo links several threads: SYBEL participant, preprint author, contact for the rare disease bundle, and presenter for Food and Nutrition at the Toxicology meeting.

## 021: feasibility of the systems biology bundle

- The planned activity was taken from the 2026 meeting report, which calls the bundle "the most concrete and widely supported idea". The other planned actions (RDMkit page, AI review paper, OpenEBench) have no comparable delivered case in the data with people attached.
- Comparator: the Rare Diseases "Systems Biology Service Bundles for Rare Diseases". The PDF acknowledgement names "Rare Disease Community Implementation study: Task 3.2 Consolidation of the ELIXIR RD Service Collection". The 2022 RD services study (Jan 2022 – Jan 2023) lists "Consolidate the recently created ELIXIR RD Service Collections (former Bundles)" as a goal, so I linked them. The PDF spells the third author "Marek Ostazewski".
- The bundle page links 3 concept maps; the document has 5 use cases.
- The bundle overview page also lists AMP4RD (May 2023, with a paper). It was not used because the data holds no author or funding detail for it.
- The verdict is a judgement, not a fact from the data. The facts behind it: the rare disease bundle had dedicated funding and three authors; the Systems Biology plan names no owner, date or funding; the meeting report notes limited engagement with Community training.
- DBTLHub, the main microbial link, ends in December 2026.
