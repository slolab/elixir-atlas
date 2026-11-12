# Access control and group management

Use LifeScience AAI and Perun as the authority for Atlas identities, groups, memberships, and group management roles. This integration direction was confirmed by the project owner on 12 November 2026. Preserve the rules below when adding authentication, restricted data, or group management to Atlas.

The key distinction is that **membership inherits upward through the group tree, while management authority comes from role assignments**. Being a manager does not make a person a member of the managed group.

For the human overview, see the [two-slide PDF](access-control-slides.pdf): a concrete membership example followed by the hierarchy and management roles.

## Authority and scope

The policy source is [Instructions for group admins — LifeScience AAI - PERUN group management tool](https://docs.google.com/document/d/1mDsVhb6YttmOR0yEx7y4bJAh9qu47ORVez_IDM9d640/edit?tab=t.0#heading=h.qhn2flx18bcr), the canonical document link supplied by the project owner. This guide was reviewed against the attached copy, `Instructions - Instructions for group managers.docx`, whose latest listed revision is 14 August 2024. References below use its section titles. This guide records the supplied version, not a verification of the current online revision or Perun interface.

The source is an operating handbook for ELIXIR platform and community leaders and other appointed managers of Node or custom groups. It explains how to use Perun to view, add, invite, approve, renew, and remove members, configure forms and notifications, and delegate management. Read it by the task being performed: membership work starts with the group's Members page, application decisions with Applications, and delegation with Advanced settings > Managers.

Treat the source-backed rules as requirements. The implementation guardrails explain how to preserve them in Atlas. Open decisions are not permission grants and must not be filled in by an agent without agreement.

The current Atlas dashboard and API serve public, read-only data, as described in [the server guide](../server/README.md) and [the dashboard guide](../dashboard/README.md). This document defines future development requirements; it does not implement authentication or change the existing public release. The database reader role is a database safeguard, not a Perun user role.

## Group hierarchy and membership

A Perun group is a named collection of user accounts used to manage membership and access. It can represent people associated with a Node, a scientific community, a platform, a working team, or another administrative purpose. It is a general access-management object, not a new organizational level above Nodes or Communities. The source does not establish a one-to-one mapping between Atlas organizational records and Perun groups.

The group named `Community` below is the broad parent container for people affiliated with ELIXIR. Do not confuse it with an individual ELIXIR scientific Community. Likewise, the `Nodes` container groups administrative membership lists; it is not itself a national Node. Use explicit mappings when linking these authority objects to Atlas records.

Groups belong to the ELIXIR virtual organization, or VO. The source describes the `Community` branch, the `Nodes` container, and custom groups. Its concrete example is:

```text
ELIXIR VO
├── Community
│   └── Interoperability
│       └── RDA Activities Focus Group
├── Nodes
└── Custom groups
```

“Custom groups” is a category in this illustration, not a required group named `Custom`.

| Rule | Required behavior |
| --- | --- |
| Direct membership | A person can be added to a specific group. |
| Inherited membership | A member of a group also belongs to every parent group. Preserve the distinction between direct and indirect membership. |
| Example | Membership in `Community:Interoperability:RDA Activities Focus Group` also gives membership in `Community:Interoperability` and `Community`. |
| Direction | Parent membership does not by itself establish membership in a child or sibling group. |
| Management separation | A group manager must be added separately to become a member of the managed group. |
| Intranet access | The source states that `Community` membership gives ELIXIR Intranet access. |
| Propagation | The source reports about five minutes for Community membership changes to reach the Intranet. This is not an Atlas synchronization guarantee. |

Source: “How do you know you are a group manager in Perun?” and “Viewing the current members of a group you manage in Perun”.

### Nodes and membership links between groups

A Node is an organizational entity whose people can be represented through configured Perun groups. The supplied handbook describes groups under the `Nodes` container, but does not provide an inventory or guarantee one group per Node.

The following platform clarification was checked against official Perun documentation on 12 November 2026. It supplements the handbook and does not establish that ELIXIR has configured any particular additional relation. Perun distinguishes a subgroup's single structural parent from additional group relations. A configured group relation can include one group's members as indirect members of another group. See [Managing members](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/1758363649/Managing%2Bmembers) and the [GroupsManager API](https://perun-aai.org/documentation/technical-documentation/core/cz/metacentrum/perun/core/api/GroupsManager.html), particularly `createGroup`, `getParentGroup`, and `createGroupUnion`.

For example, a focus group could sit under a Community and have an explicitly configured membership relation to a Node group. That would grant indirect Node-group membership to the focus group's members. A scientific or organizational association with a Node is not sufficient justification for this grant. Keep Atlas organizational relationships separate from verified Perun membership relations. Do not infer that every member of an international focus group belongs to a particular Node. The group inventory, configured relations, and intended access consequences must be confirmed before implementing such a mapping.

## Roles and delegation

Roles apply to a target group. Do not flatten these roles and membership into a single global permission ladder.

| Role or relationship | What the source establishes | Boundary |
| --- | --- | --- |
| Member | Belongs to a group directly or through inheritance. | Membership alone does not grant group administration. Atlas resource access needs its own explicit policy. |
| Group admin | Performs group administration described in the guide, including membership operations, application handling, forms, notifications, and manager assignments. | Administration does not automatically confer membership in the managed group. |
| Group membership manager | Handles applications. | Cannot perform other group administration, such as changing settings. Direct add/remove powers and other operations are not established by this source. |
| Group observer | Can view group settings. | Cannot edit settings. The source does not establish access to member lists, applications, or personal details. |

A role can be assigned to a person. A group can also be nominated to manage another group: all members of the managing group become managers of the target group. Preserve this delegation relationship and its target scope. Use the authority reported by Perun; do not guess how indirect membership or multiple assignments affect delegated roles.

The source recommends using the Group admin role alone where possible rather than assigning both admin and membership manager to the same person. This does not mean every membership manager should be promoted to admin.

Group containment is not evidence of management-role inheritance. The source does not define whether managing a parent group grants authority over descendants. Do not infer such authority from a group path. Likewise, a publicly listed leader, co-lead, affiliation, email recipient, or Atlas graph relationship is not an authenticated role assignment.

Source: “Adding members to a group you manage in Perun”, “Changing who gets notifications”, and “Viewing, adding and deleting group managers in Perun”.

## Joining and renewing membership

1. **Existing ELIXIR user:** an authorized group admin can find the person by name, login, or email and add them to the group.
2. **Person not registered:** they can register through the ELIXIR Intranet and then be added, or receive an invitation to the group's application form.
3. **Invitation:** the group needs an application form and associated email notifications. The recipient follows the invitation link and completes the form. Sending an invitation alone does not grant membership.
4. **Manual approval:** an authorized manager reviews each application and approves or rejects it.
5. **Automatic approval:** in the flow described by the source, an invited person completes the form without a further manager approval. Do not generalize this to unrestricted self-enrolment.
6. **Application type:** `INITIAL` is the first membership application. `EXTENSION` renews an existing membership that is expiring. The source gives no universal expiry period or renewal policy.

Forms support required fields, conditional display, question and help text, and separate machine values and visible labels. Copying a form or its notifications does not copy membership or grant management authority. Retain configured approval mode and application type; do not invent defaults.

Source: “Adding members to a group you manage in Perun”, “Dealing with applications”, “Creating group application forms”, and “Editing group application forms”.

## Removing membership or authority

Removing a membership removes that person's membership in the selected group and the inherited parent memberships supported by it. Keep parent membership when another child membership still supports it. Also preserve any independent direct membership reported by Perun. Do not implement removal as unconditional deletion of every ancestor membership.

Removing someone from a group does not delete their LifeScience AAI identity. Removing a manager assignment is a separate operation from removing group membership. Re-evaluate effective authority through Perun when a role assignment or membership in a managing group changes; another valid assignment may still grant authority.

The Perun workflow asks for confirmation before removing a member or a manager assignment. Preserve that distinction and confirmation in any future management interface.

Source: “Deleting members of a group you manage in Perun” and “Viewing, adding and deleting group managers in Perun”.

## Notifications and contact details

| Notification | Purpose |
| --- | --- |
| `Created/user` | Acknowledge the user's group registration. |
| `Mail validation/user` | Validate the email address supplied in the form. |
| `Created/manager` | Notify managers of a membership application. |
| `Approved/user` | Tell the applicant the application was approved. |
| `Rejected/user` | Tell the applicant the application was rejected. |
| `Invitation/user` | Invite the person to apply to the group. |

Group admins receive manager notifications by default. Adding a membership manager does not stop admin delivery. The group's “To email addresses” attribute can redirect notifications to a specified address instead of the admin. The source does not fully specify its effect on every other manager recipient.

Notification recipients and notification enablement are delivery settings, not authorization. Suppressing an approval or rejection email does not change the decision. The source permits temporary suppression and instructs managers to enable the notification again afterward. Templates can use placeholders such as `{groupName}` and `{displayName}`.

Changing the contact email through the LifeScience AAI profile changes mailing-list delivery. It does not change the login identity or login method. Do not use a mutable contact email as an Atlas authorization key.

Source: “Creating notifications”, “Editing notifications”, “Changing who gets notifications”, and “How a user can change their email address”.

## Implementation guardrails for Atlas agents

These are engineering consequences of the chosen authority and source rules, not additional Perun permissions.

- Reuse AAI authentication and Perun group authority. Do not create a parallel Atlas account, membership, or group-admin authority. A local cache or projection must remain subordinate to the source.
- Bind users, groups, and assignments to verified authority identifiers. Names, email addresses, browser-supplied claims, scraped leadership records, and colon-separated display paths are not proof of authorization.
- Keep membership, role assignment, and resource permission conceptually separate. An assignment must identify its target group. Show the distinction between direct membership, inherited membership, and management authority wherever it affects a user's decision.
- Enforce protected operations on the server. Apply the agreed resource policy consistently to details, lists, search, SQL, exports, and agent responses. Hiding a control in the dashboard does not enforce access.
- Grant protected access only when a verified identity and an explicit applicable permission justify it. Missing or ambiguous authority must not silently grant access. Public access remains governed by the explicit public-data policy.
- Do not copy restricted records into public release bundles, public search indexes, or offline agent packages. A later revocation cannot recall an already distributed copy.
- Keep the first integration small. Prefer directing administrators to Perun over rebuilding its management interface unless an Atlas interface is explicitly requested.

## Decisions required before protected features ship

| Decision still needed | What agents must not assume |
| --- | --- |
| Atlas resources and actions each group may access | Community or Intranet access does not automatically grant access to all Atlas data, editing, exports, or administration. Define the resource-to-group policy explicitly. |
| Trusted integration mechanism | The source gives no Atlas authentication protocol, claim names, API contract, or identifier mapping. Verify the chosen integration before coding against it. |
| Role capabilities not covered above | Verify descendant management, observer visibility, membership-manager operations, and delegated-role membership semantics against authoritative Perun behavior. |
| Membership status and expiry | Define how inactive, suspended, expired, or pending states affect Atlas access. An `EXTENSION` application alone is not proof of renewed membership. |
| Synchronization and revocation | Agree freshness, cache expiry, outage behavior, and revocation timing. Do not reuse the Intranet's five-minute figure as an Atlas policy. |

Record the agreed answers here before enabling the dependent feature. Keep ungranted protected capabilities unavailable while the relevant policy is unresolved.

## Acceptance scenarios for future implementation

Use these as behavioral checks when the relevant integration is built. They do not claim that the current application enforces these rules.

| Scenario | Expected result |
| --- | --- |
| A person joins RDA Activities Focus Group | They also appear as an indirect member of Interoperability and Community, with no inferred membership in siblings. |
| A person belongs only to Community | No child-group membership follows from that fact alone. |
| A person receives Group admin on a group | They can exercise the authority Perun grants, but are not automatically a member of that group. |
| A membership manager tries to change settings, or an observer tries to edit them | The operation is denied. |
| Group A manages Group B | Perun-reported members of A receive the delegated management authority over B without automatic membership in B. Removing the supporting assignment triggers an authority refresh. |
| One child membership is removed while another remains | Shared ancestor membership remains. The person's AAI identity remains. |
| An invitation is sent, or a manual application remains pending | Neither is treated as approved membership. An invited automatic application requires form completion. |
| An admin receives an application notification, or an address is added to notification recipients | Delivery does not create a new role assignment. |
| A contact email changes | Mailing delivery changes without creating a new Atlas identity or changing permissions. |
| A protected resource is queried through search, SQL, export, or an agent | The same resource policy applies as through its normal endpoint. Unauthorized content does not appear in results or derived output. |

## Operational contacts from the source

- For a missing manager role under `Community`, contact the ELIXIR Hub at `webmaster@elixir-europe.org`.
- To request a group under `Nodes` or a custom group, contact `support@aai.lifescience-ri.eu`.
- The main management URL given is [LifeScience AAI Perun](https://perun.aai.lifescience-ri.eu/). One later section retains an older ELIXIR Czech URL; do not hard-code that discrepancy into Atlas.

These are support routes, not definitions of global application privileges. The source's operational instructions do not authorize agents to send invitations, contact support, or change real memberships without a task requesting those actions.
