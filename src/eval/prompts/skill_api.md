Use the Agentic ELIXIR skill at `/workspace/.agents/skills/agentic-elixir/SKILL.md` and its API reference to answer the question. Read the skill before searching. The API base URL for this run is `$api_url`.

The skill and this API are your only evidence sources. No raw data, local graph, source index or reference answers are provided. Web search and fetching external source pages are unavailable; cite the original URLs or DOIs returned by the API.

Keep the complete body of every API response you fetch under `/workspace/evidence`, including responses fetched by scripts. Keep a `requests.jsonl` there with the HTTP method, URL, complete request body (including SQL), HTTP status and saved response filename so the evidence can be matched to your tool calls after the run. Record request IDs when available. Preserve failed queries and their responses. These files are collected with your answer and the agent trace. Do not put credentials in them.

`curl`, `jq`, `python3` and `rg` are installed.
