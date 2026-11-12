import type { OverlapData } from "../types";
import { useState } from "react";
import { Table, Empty, RequestState } from "../components";
import { apiUrl, useApi } from "../db";
import { href } from "../route";

export function Overlap() {
  const [liaisons, setLiaisons] = useState(false);
  const { data, error } = useApi<OverlapData>(apiUrl("overlap", { liaisons }));
  const pairs = data?.pairs ?? [];
  return (
    <>
      <h1 className="page-title">Groups that share leaders</h1>
      <p className="lede">
        Pairs of Communities, Platforms, Focus Groups and other groups with more than one person in a leading role in both.
      </p>
      <div className="filters" role="group" aria-label="Options">
        <label>
          <input type="checkbox" checked={liaisons} onChange={(event) => setLiaisons(event.target.checked)} /> Count Hub liaisons
        </label>
      </div>
      {!data ? <RequestState error={error} /> : pairs.length ? (
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
    </>
  );
}
