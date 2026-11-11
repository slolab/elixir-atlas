import { useMemo, useState } from "react";
import { Empty, More, Section } from "../components";
import { rows } from "../db";
import { label } from "../format";
import { href } from "../route";

const LEADING = ["lead", "co_lead", "chair", "coordinator", "deputy", "work_package_lead", "task_lead"];

type Holder = { id: string; name: string; places: number; detail: string };
type Pair = { first: string; first_name: string; second: string; second_name: string; shared: number; people: string };

export function Overlap() {
  const [liaisons, setLiaisons] = useState(false);
  const [groupsOnly, setGroupsOnly] = useState(false);
  const [minimum, setMinimum] = useState(3);
  const kinds = liaisons ? [...LEADING, "liaison"] : LEADING;
  const marks = kinds.map(() => "?").join(",");
  const family = groupsOnly ? "and i.family = 'group'" : "";
  const holders = useMemo(
    () =>
      rows<Holder>(
        `select id, name, count(distinct initiative) places, group_concat(kind || '|' || initiative || '|' || initiative_name, '§') detail
         from (
           select distinct p.id, p.name, h.role_kind kind, i.id initiative, i.name initiative_name
           from HoldsRole h join Person p on p.id = h.source join Initiative i on i.id = h.target
           where h.role_kind in (${marks}) ${family}
         )
         group by id having places >= ? order by places desc, name`,
        [...kinds, minimum],
      ),
    [marks, family, minimum, liaisons],
  );
  const pairs = useMemo(
    () =>
      rows<Pair>(
        `select a.target first, ia.name first_name, b.target second, ib.name second_name, count(distinct a.source) shared,
           group_concat(distinct p.name) people
         from HoldsRole a join HoldsRole b on a.source = b.source and a.target < b.target
         join Initiative ia on ia.id = a.target join Initiative ib on ib.id = b.target join Person p on p.id = a.source
         where a.role_kind in (${marks}) and b.role_kind in (${marks}) and ia.family = 'group' and ib.family = 'group'
         group by a.target, b.target having shared > 1 order by shared desc, ia.name limit 60`,
        [...kinds, ...kinds],
      ),
    [marks, liaisons],
  );
  return (
    <>
      <h1 className="page-title">Who carries several leading roles</h1>
      <p className="lede">
        Leading roles are lead, co-lead, chair, coordinator, deputy and work package or task lead. Roles come from the pages and documents in the snapshot, so a missing page means a missing role.
      </p>
      <div className="filters" role="group" aria-label="Options">
        <label>
          <input type="checkbox" checked={liaisons} onChange={(event) => setLiaisons(event.target.checked)} /> Count Hub liaisons
        </label>
        <label>
          <input type="checkbox" checked={groupsOnly} onChange={(event) => setGroupsOnly(event.target.checked)} /> Groups only
        </label>
        <label>
          At least{" "}
          <select value={minimum} onChange={(event) => setMinimum(Number(event.target.value))}>
            {[2, 3, 4, 5, 6].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>{" "}
          places
        </label>
      </div>
      <Section title="People" note={`${holders.length} people hold leading roles in at least ${minimum} places.`}>
        {holders.length ? (
          <More
            items={holders}
            limit={25}
            render={(shown) => (
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Person</th>
                    <th scope="col" className="number">Places</th>
                    <th scope="col">Where</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.map((holder) => (
                    <tr key={holder.id}>
                      <td>
                        <a href={href("person", holder.id)}>{holder.name}</a>
                      </td>
                      <td className="number">{holder.places}</td>
                      <td className="places">
                        {holder.detail.split("§").map((part) => {
                          const [kind, id, ...name] = part.split("|");
                          return (
                            <span key={part}>
                              <a href={href("initiative", id)}>{name.join("|")}</a> <span className="muted">{label(kind).toLowerCase()}</span>
                            </span>
                          );
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          />
        ) : (
          <Empty>Nobody holds that many leading roles. Lower the number of places.</Empty>
        )}
      </Section>
      <Section title="Groups that share leaders" note="Pairs of Communities, Platforms, Focus Groups and other groups with more than one person in a leading role in both.">
        {pairs.length ? (
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Group</th>
                <th scope="col">And group</th>
                <th scope="col" className="number">Shared</th>
                <th scope="col">People</th>
              </tr>
            </thead>
            <tbody>
              {pairs.map((pair) => (
                <tr key={`${pair.first}-${pair.second}`}>
                  <td>
                    <a href={href("initiative", pair.first)}>{pair.first_name}</a>
                  </td>
                  <td>
                    <a href={href("initiative", pair.second)}>{pair.second_name}</a>
                  </td>
                  <td className="number">{pair.shared}</td>
                  <td className="muted">{pair.people.split(",").join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty>No two groups share more than one leader.</Empty>
        )}
      </Section>
    </>
  );
}
