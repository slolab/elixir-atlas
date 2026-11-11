import initSqlJs, { type Database, type SqlValue } from "sql.js";
import wasmUrl from "sql.js/dist/sql-wasm-browser.wasm?url";

export type Row = Record<string, SqlValue>;

let database: Database | null = null;

export async function openAtlas(): Promise<void> {
  const [SQL, response] = await Promise.all([initSqlJs({ locateFile: () => wasmUrl }), fetch("/graph.sqlite")]);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  database = new SQL.Database(new Uint8Array(await response.arrayBuffer()));
  for (const table of rows<{ name: string }>("select name from sqlite_master where type = 'table'")) {
    const columns = rows<{ name: string }>(`select name from pragma_table_info('${table.name}')`).map((column) => column.name);
    if (columns.includes("source") && columns.includes("target")) {
      database.run(`create index if not exists "${table.name}_source" on "${table.name}"(source)`);
      database.run(`create index if not exists "${table.name}_target" on "${table.name}"(target)`);
    }
  }
}

export function rows<T = Row>(sql: string, params: SqlValue[] = []): T[] {
  if (!database) {
    throw new Error("The atlas database is not open yet.");
  }
  const statement = database.prepare(sql);
  statement.bind(params);
  const result: Row[] = [];
  while (statement.step()) {
    result.push(statement.getAsObject());
  }
  statement.free();
  return result as T[];
}

export function one<T = Row>(sql: string, params: SqlValue[] = []): T | undefined {
  return rows<T>(sql, params)[0];
}

export function list(value: SqlValue | undefined): string[] {
  if (typeof value !== "string" || !value) {
    return [];
  }
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}
