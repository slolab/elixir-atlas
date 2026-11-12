import type { OverlapData } from "../types";
import { useState } from "react";
import { Table, Empty, RequestState, More, Section } from "../components";
import { apiUrl, useApi } from "../db";
import { label } from "../format";
import { href } from "../route";

export function Overlap() {
  const [liaisons, setLiaisons] = useState(false);
  const [groupsOnly, setGroupsOnly] = useState(false);
  const [minimum, setMinimum] = useState(3);
  const { data, error } = useApi<OverlapData>(apiUrl("overlap", { liaisons, groups_only: groupsOnly, minimum }));
  const { holders, pairs } = data ?? { holders: [], pairs: [] };
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
      {!data ? <RequestState error={error} /> : null}
      {data ? <>
      <Section title="People" note={`${holders.length} people hold leading roles in at least ${minimum} places.`}>
        {holders.length ? (
          <More
            items={holders}
            limit={25}
            render={(shown) => (
              <Table className="table">
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
              </Table>
            )}
          />
        ) : (
          <Empty>Nobody holds that many leading roles. Lower the number of places.</Empty>
        )}
      </Section>
      <Section title="Groups that share leaders" note="Pairs of Communities, Platforms, Focus Groups and other groups with more than one person in a leading role in both.">
        {pairs.length ? (
          <Table className="table">
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
          </Table>
        ) : (
          <Empty>No two groups share more than one leader.</Empty>
        )}
      </Section>
      </> : null}
    </>
  );
}
