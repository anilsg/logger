<!-- vim: set ft=markdown spell: -->

# Remote Logging Service

- **Title:**    Logger Server
- **Date:**     2017-11-30
- **Subject:**  Independent logging REST service
- **Author:**   Anil (Neil) Gulati

## Overall description

We want to accumulate errors and miscellaneous events on a central server. For this, we need to implement a two-fold application:

- **Client side library**, seamlessly integrated into current infrastructure with minimal set of extra requirements.
- **Server side**, working on a separate server, and available over the network to accept error messages and provide API for the clients to process and visualize these messages.

## Independent Logging Server

- **Client:**    Simple library to log a message: logger_client.py.
- **Server:**    Remote server receives messages on REST API (POST only): logger_server.py.
- **Server:**    Remote server also presents REST API for analysing logs (GET only).
- **Server:**    Remote server potentially may respond to DELETE to flush old logs early but otherwise automates rolling deletion.
- **Collector:** Worker on remote server processes messages dumped in cache by server. logger_collector.py.

## Logger Client

Logging to the remote logging server is supported by the standard library HTTP logger.
Extra name value pairs for logging in addition to the message can be supplied in the record dict.

Usage:

        import remote_logger
        logger = remote_logger.getLogger(__name__)
        ...
        record = { 'name':'value', 'other_name':'other_value' }
        logger.log(40, 'Static error message.', extra=record)
        ...
        remote_logger.shutdown()

Example of some of the values passed:

- created=1512386686.0873692
- name=test_facility
- levelno=50
- levelname=CRITICAL
- msg=Something went wrong message.

### Fields

- **facility:**     Unique name supplied by logger to tag this message source.
- **created:**      Logger provides a timestamp at the time the message was created.
- **level:**        Normal log levels supported: emerg alert crit error warn notice info debug.
- **message:**      Fixed string describing the particular error from this particular facility.
- **additional:**   Additional arbitrary name / value pairs can be sent to log context and state from the error such as: exception, headers, user-id, user-email, etc.

### Authentication

- Run HTTPS server with basic auth.
- Logging information may include user data so need to run HTTPS.
- Possibly IP address authentication could be applied, shared secret HMAC signature...
- Could provide additional API to dispense tokens based on a supplied secret, where tokens expire. Probably too much work for little benefit.

### POST API

- POST /api/v1/eventlog
- POST API is taken care of by logging handler.
- POST API consists of one route and all parameters included are url-encoded.
- Refer also to doc strings.

Messages must POST to /api/v1/messages with these parameters.
Parameters align to those generated and used by logging standard library module.

- created:    datetime timestamp generated by the logger like this: 1512386686.0873692.
- name:       Facility name (given to logger on creation), using usual identifier syntax: alphanumeric, underscore, no spaces.
- levelno:    The usual logging level numeric equivalent: emerg=70 alert=60 crit=50 error=40 warn=30 notice=25 info=20 debug=10. Two decimal digits expected.
- msg:        Static string description of error, without embedded formatting or variables, to support counting.
- name/value: Additional arbitrary name/values allowed and will be logged (clients need to co-ordinate the same names for analysis).

E.g. curl -i -d 'name=facility_name' -d 'levelno=40' -d 'msg=This is the error message.' -d 'created=1512386686.123456' -d 'additional_key=additional_value' http://hostname:8080/api/v1/messages

### GET API

Several GET APIs are presented, with some common elements between all of them. (Not yet implemented).
All GET responses are returned in JSON.

#### Resource Paths

Resource paths are all presented by day, hour and minute.

Therefore for a given resource `resource` the following can all be queried:

- **/api/v1/resource/**:                 Returns the range of date times available for this resource as a start, end, duration.
- **/api/v1/resource/YYYYMMDD/**:        Returns the resource for the whole of this day.
- **/api/v1/resource/YYYYMMDD/HH/**:     Returns one hour of the resource.
- **/api/v1/resource/YYYYMMDD/HH/MM/**:  Returns one minute of the resource.

#### Pagination

- Pagination is determined by a `duration` in minutes `since` a particular minute.
- Pagination can be requested by the client providing these two values, and can be forced by the server if determined due to bulk of response.
- Pagination doesn't need to be managed since the number of minutes in an hour or a day are known in advance by both server and client.
- Pagination `duration` and `since` values are always in minutes within the context of the day or hour of the resource supplied as parameters and returned by the server.
- E.g. resource/20171203/00?duration=60&since=0 returns the first 60 minutes on 3 Dec after midnight.
- Server will not return logs for the current minute, and possibly a few minutes in arrears.
- Server may elect to return different `duration` and `since` values than those supplied.

#### Filters

- Simple well known filters are provided by parameter for facility name, level, and error message.
- Parameters are `facility=<name>`, `level=<DD>` and `message=<string>`.
- Plus / space separated lists of values can also be provided for facility and level.
- Refer also to tagging in further ideas. A separate API can be used to define tags which are then submitted as a parameter `tag=<tagname>` to elicit that filtering.
- Filtering on additional extra data submitted with the log records can also be applied.
  All `name=value` parameters submitted with a query if not understood by other features will be applied as additional content filters e.g. `user-id=joeblow`.

#### Counts

- /api/v1/counts/
- Provides total counts over the period requested by facility, level and message.
- When requested for a day counts are returned per hour.
- When requested for an hour counts are returned per minute.
- Finer granularity is not available since the API determines only to whole minutes.
- Pagination is not used for this resource.
- Filtering can be applied.

#### Messages

- /api/v1/messages/
- Provides just the facility, level, date time and message string for all messages received with the period requested.
- Pagination applies as described.
- Filtering can be applied.

#### Full Messages

- /api/v1/fullmessages/
- Provides entire message content for all messages received with the period requested.
- Pagination applies as described.
- Filtering can be applied.

#### Types

- /api/v1/types/
- Provides an exhaustive list of all key values occurring in messages within the period requested.
- Therefore a list of all levels, all facilities, all error messages, as well as composited key values from the additional records.
- Pagination is not used for this resource.
- Filtering is not used for this resource.

### Testing

- Not implemented yet.
- Use pytest, but mock too awkward and involved with httpd.
- Use a test client that checks responses from the server running locally, but problems checking logged output for this too.
- Unit tests are not supposed to include complex dependencies like servers but this is a simple server run locally so testing will be reliable.
- This also avoids the problems that can come from mocking where the mock is out of date or fails to replicate fully and causes false positives or negatives itself.

### Problems

- Not clear on the scale: 4 million messages in a 3 hour period, 370 requests per second?
- Judging by the example graphic there may be up to 500 log events per second.
- May be an issue with clock skew when trusting timestamps from clients. Alternatively generate a server timestamp only.

### Further ideas

#### Tagging

- Support an API to allow individual users to define tags as a collection of search parameters available.
- Then support GET API based on those tags.

#### Filtering and searching

- Filtering by extra parameters or message content could be provided.
- When compiling GET response just select lines which match 'user_id=<user_id>'. URL-encoded lines support this with no further work.

#### Message expiry and depreciation.

- Simple with this model to add automated step in the collector to old out unwanted data.
- It's all stored by day as well so it's easy to select a set of log file names starting with the date and just remove them.
- DELETE API could support early flushing on demand.

#### To do

- write get method to return logs
- write delete method and automate call at appropriate intervals
- write example js web app to present stats
- api documentation
- unit test framework
- Add SSL support and basic auth. Can read userid/password from a file, if don't want to hard code.
- Add forking for the server if required to improve performance.
- Further commenting and description in README.md and doc strings.
- Can spawn multiple sub-processes for collector if required to improve performance, allocating individual log files to dedicated process.
- Using a local cache on the client, with a separate process to send messages to the server would also improve reliability.
  This would also cover the client for when the logging server goes down.
- Expiry and deletion of old log files.
- Additional exception detection in the collector to ensure reliable.
- Catch server down in logger.

