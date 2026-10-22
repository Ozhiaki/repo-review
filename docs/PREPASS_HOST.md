# Connect a host to Prepared Review

Prepared Review supplies an MCP source service. The host remains responsible for the model session, prompt delivery, report storage, and any usage records. The service does not run a model.

## Load a connection

The `connect` command writes an MCP configuration that starts `prepare_review.py serve CONNECTION_CONFIG` with the same Python executable used for setup. That Python environment needs tiktoken 0.12.0.

Use the printed configuration in your host. Give the agent only the current handoff. The connection selects one pass. Comparison source requests are refused outside pass 04. The service exposes captured source only, not operator-held prompt files.

The tools are:

| Tool | Purpose | Reading credit |
|---|---|---|
| `lookup` | Locate paths, symbols, call spellings, modules, imports, literal text, or leads | None |
| `read_source` | Read captured source for a stated question | Pending until observed by a compatible host |
| `coverage` | Report confirmed ranges for a selected file | Reports delivery only |

Source ranges use one-based LF line coordinates. Both range bounds are required. Each response is limited to 16,384 source bytes. The source question must contain 8 to 600 characters. Lookup is paged. The call limit is 256 per pass across attempts in the same state directory.

The service checks captured file hashes. It refuses paths outside the selected inventory, binary files, and LFS pointers. Lookup and source text remain evidence, not instructions to the agent.

## Confirm actual delivery

A generated response is not proof that the host delivered it. The source service writes a `produced` record before returning the response. It grants no reading credit at that point.

The trusted host must observe the successful tool result that it actually supplies to the agent. It must preserve the returned source bytes and verify their length and hash against the produced record. Error, truncated, missing, or mismatched results must remain unconfirmed.

The extracted Claude Code adapter is `prepared_review.host_capture.Observer`. It has no model client or launcher. Host code can use it as follows:

```python
from prepared_review.host_capture import Observer

observer = Observer(attempt_directory, session_id)
for event in delivered_host_events:
    observer.event(event)
```

`delivered_host_events` must come from the real host boundary. It must include the assistant tool call and its corresponding user tool result. The adapter recognizes `mcp__review__read_source`. A server stdout log is not a substitute for those events.

The adapter writes `captures/` and `delivered/` under that attempt. It does not grant model-supplied self-confirmation. Do not expose the adapter as a review tool.

Other hosts need their own compatible observation. Without one, reviews can still read source, but `coverage` remains unconfirmed. Do not invent receipts to remove that limit.

## Keep the meaning of coverage narrow

Confirmed ranges can combine across passes for the same source hash. Lookup hits and packet facts do not count as complete source reads. Delivery does not prove that the agent understood the source or wrote a valid finding.

The read-only tool annotations refer to subject source. The service writes its own call and delivery records in the separate state directory.

## Preserve context and records

The normal workflow delivers passes one at a time to the same conversation. A host can use a fresh conversation when needed, but it must supply the current style guide and relevant prior reports. It must record that change when comparing results.

Method, model, and reasoning settings are separate choices. Prepared Review does not force Sonnet or an effort level. The old experiments used fixed settings for their comparisons. Those settings are historical evidence, not service defaults.

Keep raw host responses and originals when a report fails format validation. A format-only amendment should be a separate file. Do not repeat completed paid analysis just to repair its format.
