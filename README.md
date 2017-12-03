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
- Almost certainly should run HTTPS since user information may be available in the error messages.
- Could run HTTPS with a HMAC signed request but that's probably not required?
- Possibly IP address authentication could be applied, or basic auth.
- Could provide additional API to dispense tokens based on a supplied secret, where tokens expire. Probably too much work for little benefit.

### Pagination

- Return by minutes worth of messages since a particular minute.
- This provides / eliminates pagination since the historical resource won't change once the minute has passed.
- Server will not return logs for the current minute.
- May be an issue with clock skew. Consider trusting timestamps from clients or alternatively generate a server timestamp only.
- May also return by hour or day, depending on the volume of the response, but these would be implemented as alternative resources.

### Testing

- pytest, mock too awkward and involved with httpd.
- Use a test client that checks responses from the server running locally, but problems checking logged output for this too.
- Unit tests are not supposed to include complex dependencies like serves but this is a simple server run locally so testing will be reliable.
- This also avoids the problems that can come from mocking where the mock is out of date or fails to replicate fully and causes false positives or negatives itself.
- Judging by the example graphic there may be up to 500 log events per second.

### Clients

- Don't use logging handlers because they are thread safe but not process safe, and they also constrain the passing of data.
- Using a local cache with a separate process to send messages to the server would also improve reliability.
- This could also cover the client for when the logging server goes down.

### Problems

- Not clear on the scale: 4 million messages in a 3 hour period, 370 requests per second?
- Running a single process per log file to aggregate messages needs to be able to sink peak message rate.

### Further ideas

### To do

- write log method to store messages: use logger or write file?
- write client to provide log method and pass to server: use request or logger?
- write get method to return logs
- write delete method and automate call at appropriate intervals
- write example js web app to present stats
- add authentication
- document api
- testing


