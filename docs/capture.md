# Capture

Python SDK 0.5.5 and Node SDK 0.4.3 use capture binary 0.3.6. The Python capture
extra installs it.

```bash
pip install 'videodb[capture]'
```

Supported: macOS 13+ on Apple Silicon and Intel, Windows x64, and Linux x64 on
Ubuntu 22.04+ with PipeWire and xdg-desktop-portal plus a ScreenCast backend.
There is no Linux ARM64 binary.

## API correspondence

Python keeps snake_case arguments and native response/event keys (such as
`recordingId`, `sessionId`, `managedDeferredRecording`). Node uses camelCase
arguments. Python timeouts are **seconds**; Node `timeoutMs` is milliseconds.

| Python | Node | Contract |
|---|---|---|
| `get_capabilities()` | `getCapabilities()` | Managed boolean plus optional resolutions, notices, instant-start fields; absent fields stay absent |
| `start_session(id, channels, resolution=...)` | `startSession({sessionId, channels, resolution})` | Native start acknowledgement, optional recording ID; live readiness arrives separately |
| `stop_session()` | `stopSession()` | Stops live capture; does not mean processing completed |
| `start_recording(...)` | `startRecording({...})` | Authorized deferred capture; requires owner, collection, fresh token, channels |
| `stop_recording(timeout=...)` | `stopRecording({timeoutMs})` | Waits for local finalization readiness |
| `list_recordings(owner)` | `listRecordings({owner})` | Owner-scoped recovery; adopts listed jobs and can invoke token provider |
| `list_local_recordings()` | `listLocalRecordings()` | Session-backed job history; listing itself does not relay |
| `relay_recording(id, token, owner=...)` | `relayRecording({...})` | Fresh authorization; acceptance is not ingestion completion |
| `wait_for_processing(recording_id=... / session_id=...)` | `waitForProcessing({...})` | Exactly one target; caches early completion, rejects final failure/exit/timeout |
| `shutdown(wait_for_processing=False)` | `shutdown({waitForProcessing:false})` | Explicitly suspend pending delivery for recovery |
| `pause_tracks([...])`, `resume_tracks([...])` | `pauseTracks([...])`, `resumeTracks([...])` | Legacy track names or selected channel IDs (0.3.6+) |
| `get_notices()` | `getNotices()` | Active notices; also consume `recording-notice` events |
| `get_windows()` | `getWindows()` | Native capabilities; Linux portal support must be read from the result |
| `switch_window(...)`, `set_window_enabled(...)` | `switchWindow(...)`, `setWindowEnabled(...)` | Window selection and privacy controls |
| `get_permission_status(kind)` | `getPermissionStatus(kind)` | Read without prompting |
| `generate_recorder_token(collection_id, user_id)` | `generateRecorderToken({...})` | Backend-only fresh token with resolved collection ID |
| `generate_client_token(expires_in, user_id)` | `generateClientToken(expiresIn, userId)` | Existing token API gains optional user identity |

Compatibility differences: Python `request_permission()` retains its boolean
result, while Node returns a status string; use `get_permission_status()` for
precise status. Python accepts `screen_capture` and `screen-capture`. Existing
Python `Channel.store` defaults to false; Node plain channel configurations
default to true. Set `store` explicitly when sharing a configuration. Python
`events()` yields native envelopes; Node uses named EventEmitter listeners and
retains its historical colon-separated aliases. The old Node-only tokenless
`startLocalRecording()` adapter is not introduced in Python: current managed
artifacts reject tokenless capture.

## Authorized recording

Resolve authorization on the trusted backend. The desktop must not hold an API
key. Verify ownership before refreshing a retained job; never authorize solely
because a job exists on disk. `generate_recorder_token()` returns `token` and
`collectionId` (the resolved collection, even when requesting `default`).

```python
from videodb.capture import CaptureClient, AudioChannel

# authorization comes from your authenticated backend.
client = CaptureClient(base_url=api_url)
started = await client.start_recording(
    owner=user_id,
    collection_id=authorization['collectionId'],
    upload_token=authorization['token'],
    channels=[AudioChannel('mic:default', 'Microphone')],
    live=False,
    resolution='720p',
)
# Capture until the user asks to stop.
await client.stop_recording()
completed = await client.wait_for_processing(recording_id=started['recordingId'])
video_id = completed['result']['videoId']
await client.shutdown()
```

Run examples inside an async function. `live=False` belongs only on authorized
`start_recording()`, which also sends `mode: deferred` for older binaries. Audio
only is supported; otherwise select at most one display/window and optional
default microphone/system audio. Empty selections are invalid. Resolution is
`720p` or `1080p`; native errors retain `CaptureCommandError.code`.

## Events and delivery

Consume `client.events()` in a background async task before starting capture.
Each yielded envelope has `event` and `payload`. `recording-started` / the start
response means local capture is running. Wait for `recording-live` before using
live streams. `LIVE_UNAVAILABLE` means local capture continues without live
streams. Meeting detection, window events, processing progress, and notice
activation/clearing are forwarded unchanged. Ignore unknown notice codes.

Stop readiness (`recording-ready`, `local-recording-ready`, `recording-complete`)
is not server ingestion success. Only `processing-complete` confirms delivery.
`retrying: true` keeps processing waits open; `retryable` alone does not. Shutdown
normally stops capture and waits for tracked delivery. Final processing failure
or timeout leaves the process running; fix authorization or explicitly suspend.
Delayed retries can be retained for recovery rather than blocking shutdown.

Supply an async `get_recorder_token` callback to automate refresh. It receives
native identity fields and `forceRefresh: True`; managed jobs include owner and
collection, session jobs include session ID. Return a fresh token or `None` for
an unrelated job. Use either automatic refresh or manual event handling, not both.
The default refresh limit is three; managed attempts reset only on measured
sending/server progress, not relay acceptance. Reusing a token is rejected and
provider exceptions are sanitized. The callback should bound its own HTTP calls.

`list_recordings(owner)` adopts only matching-owner jobs. Listing may request
tokens and resume delivery when a provider is configured. For manual recovery,
create a client without a provider, list authorized jobs, issue fresh tokens via
your backend, relay each selected job, and await processing completion. Keep the
same API environment and owning user. Do not blindly relay failed/incomplete jobs.
