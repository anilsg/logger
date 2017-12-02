<!-- vim: set ft=markdown spell: -->
# logger

- **Title:**    Logger
- **Date:**     2017-11-30
- **Subject:**  Independent Logging Server
- **Author:**   Anil (Neil) Gulati

## Independent Logging Server

- **Client:**   Simple library to log a message.
- **Server:**   Remote server receives messages on REST API (POST only).
- **Server:**   Remote server also presents REST API for analysing logs (GET only).
- **Server:**   Remote server potentially may respond to DELETE to flush old logs early but otherwise automates rolling deletion.

### Fields

- **facility:**     Unique name supplied by logger to tag this message source.
- **timestamp:**    Logger provides a UTC timestamp.
- **level:**        Typical log levels supported: emerg alert crit error warn notice info debug.
- **event:**        Fixed string (no embedded variable parameters) that describes the particular error from this particular facility.
- **additional:**   Additional arbitrary name / value pairs can be sent to log context and state from the error such as: exception, headers, user-id, user-email, etc.

### POST API

- POST /api/v1/eventlog
- DELETE /api/v1/eventlog
- Unique IDs generated from facility and timestamp?

### GET API

- GET /api/v1/eventqry/// ???

### Authentication

- Run HTTPS server with self signed certificate only available to logging clients.
- Run HTTP server and use a shared secret used to generate an HMAC based on facility, level and timestamp, to sign the submission.

### Pagination

- Return by minutes worth of messages since a particular minute.
- This provides / eliminates pagination since the historical resource won't change once the minute has passed.
- Server will not return logs for the current minute.
- May be an issue with clock skew. Consider trusting timestamps from clients or alternatively generate a server timestamp only.
- May also return by hour or day, depending on the volume of the response, but these would be implemented as alternative resources.

### Problems

### Further ideas

## Implementation

