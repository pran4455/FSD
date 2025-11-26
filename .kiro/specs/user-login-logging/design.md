# Design Document

## Overview

The user login/logout logging system will track all authentication events in the Financial Services Dashboard application by writing structured log entries to a text file. The system will integrate with existing authentication routes (`/login`, `/verify_totp`, `/logout`) to capture login attempts, TOTP verification, and logout events without disrupting the user experience.

The logging system will use Python's built-in `logging` module with a dedicated file handler to ensure thread-safe writes, proper formatting, and error handling. Each log entry will contain timestamp, username, event type, status, and additional context in a structured format that is both human-readable and machine-parseable.

## Architecture

The logging system follows a modular architecture with clear separation of concerns:

1. **Logger Module**: A dedicated logging utility that configures and manages the file-based logger
2. **Authentication Event Logger**: Functions that create structured log entries for different authentication events
3. **Integration Points**: Minimal modifications to existing route handlers to call logging functions

The system uses Python's `logging` module which provides:
- Thread-safe file writes (important for concurrent Flask requests)
- Automatic file creation and rotation capabilities
- Structured formatting with timestamps
- Error handling that won't crash the application

## Components and Interfaces

### 1. Logger Configuration Module

**File**: `auth_logger.py`

**Purpose**: Configure and provide access to the authentication logger

**Functions**:
- `setup_auth_logger()`: Initializes the logger with file handler and formatter
- `get_auth_logger()`: Returns the configured logger instance

**Configuration**:
- Log file path: `logs/auth_events.log`
- Log format: `%(asctime)s | %(levelname)s | %(message)s`
- Date format: `%Y-%m-%d %H:%M:%S`
- Log level: INFO

### 2. Authentication Event Logger

**File**: `auth_logger.py`

**Purpose**: Provide convenience functions for logging different authentication events

**Functions**:

```python
def log_login_attempt(username: str, success: bool, auth_method: str, reason: str = None)
def log_totp_verification(username: str, success: bool)
def log_logout(username: str, session_duration: float = None)
```

**Log Entry Format**:
```
YYYY-MM-DD HH:MM:SS | INFO | EVENT_TYPE | username=<user> | status=<SUCCESS/FAILED> | method=<method> | reason=<reason> | duration=<seconds>
```

### 3. Integration with Existing Routes

**Modified Files**: `app.py`

**Integration Points**:
1. `/login` route - Log password authentication attempts
2. `/verify_totp` route - Log TOTP verification attempts
3. `/logout` route - Log logout events with session duration

**Implementation Approach**:
- Import `auth_logger` module at the top of `app.py`
- Add logging calls after authentication logic but before redirects
- Wrap logging calls in try-except to prevent logging failures from affecting authentication
- Calculate session duration by storing login timestamp in session

## Data Models

### Log Entry Structure

Each log entry follows this structure:

```
<timestamp> | <level> | <event_type> | username=<username> | status=<status> | [additional_fields]
```

**Fields**:
- `timestamp`: ISO 8601 format (YYYY-MM-DD HH:MM:SS)
- `level`: INFO for normal events, WARNING for failed attempts
- `event_type`: LOGIN, TOTP_VERIFY, LOGOUT
- `username`: The username attempting authentication
- `status`: SUCCESS or FAILED
- `auth_method`: PASSWORD, TOTP, LEGACY (for non-TOTP users)
- `reason`: Failure reason (invalid_password, invalid_totp, user_not_found)
- `duration`: Session duration in seconds (for logout events)

**Example Log Entries**:
```
2024-01-15 10:30:45 | INFO | LOGIN | username=john_doe | status=SUCCESS | method=PASSWORD
2024-01-15 10:30:50 | INFO | TOTP_VERIFY | username=john_doe | status=SUCCESS
2024-01-15 10:31:00 | WARNING | LOGIN | username=jane_smith | status=FAILED | method=PASSWORD | reason=invalid_password
2024-01-15 11:45:30 | INFO | LOGOUT | username=john_doe | status=SUCCESS | duration=4485.5
```

### Session Tracking

To calculate session duration, we'll store the login timestamp in the Flask session:

```python
session['login_timestamp'] = datetime.now().timestamp()
```

On logout, we calculate duration:
```python
duration = datetime.now().timestamp() - session.get('login_timestamp', 0)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing the acceptance criteria, several properties can be consolidated:
- Properties 1.5 and 2.3 both test immediate file writing - combined into Property 2
- Properties 4.2 and 4.3 both test error resilience - combined into Property 6
- Properties 1.1, 1.2, 1.3, 1.4 test different event types but share the same underlying property - combined into Property 1
- Properties 3.1 and 3.3 both relate to log format consistency - combined into Property 4

### Correctness Properties

Property 1: All authentication events create log entries
*For any* authentication event (successful login, failed login, TOTP success, TOTP failure, logout), the system should create a log entry in the Login Log File containing the username, timestamp, event type, and status.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1**

Property 2: Log entries are persisted immediately
*For any* authentication event, after the logging function returns, the log entry should be immediately readable from the Login Log File without requiring application shutdown or explicit flush.
**Validates: Requirements 1.5, 2.3**

Property 3: Session duration is calculated correctly
*For any* logout event, the session duration in the log entry should equal the time difference between the login timestamp and logout timestamp within a reasonable tolerance (±2 seconds).
**Validates: Requirements 2.2**

Property 4: Log entries follow consistent format
*For any* log entry in the Login Log File, parsing the entry should successfully extract timestamp, event type, username, and status fields, and each entry should be on a separate line.
**Validates: Requirements 3.1, 3.3**

Property 5: Log file is created when missing
*When* the Login Log File does not exist and an authentication event occurs, the system should create the file and write the log entry successfully.
**Validates: Requirements 3.2**

Property 6: Logging failures do not block authentication
*For any* authentication attempt, if the logging operation fails (due to file permissions, disk space, or other I/O errors), the authentication flow should complete successfully without raising exceptions to the user.
**Validates: Requirements 4.2, 4.3**

## Error Handling

The logging system must be resilient and never interfere with the authentication process:

1. **File I/O Errors**: All logging operations will be wrapped in try-except blocks. If file writing fails, the error will be logged to stderr but authentication will proceed.

2. **Permission Errors**: If the log file or directory is not writable, the system will attempt to create the directory or file with appropriate permissions. If this fails, authentication continues.

3. **Disk Space**: If disk space is exhausted, logging will fail silently and authentication will proceed. The application should not crash.

4. **Concurrent Writes**: Python's logging module handles concurrent writes safely using locks, preventing corruption from simultaneous requests.

5. **Missing Session Data**: If session data (like login_timestamp) is missing during logout, the system will log the logout event without duration rather than failing.

**Error Handling Strategy**:
```python
try:
    log_authentication_event(...)
except Exception as e:
    # Log to stderr for debugging but don't raise
    print(f"Logging error: {e}", file=sys.stderr)
    # Authentication continues normally
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual logging functions work correctly:

1. **Test log entry creation**: Verify that calling `log_login_attempt()` creates a properly formatted log entry
2. **Test file creation**: Verify that the log file is created if it doesn't exist
3. **Test log parsing**: Verify that log entries can be parsed to extract all fields
4. **Test error handling**: Verify that logging failures don't raise exceptions

**Testing Approach**:
- Use temporary directories for test log files
- Mock file I/O to simulate failures
- Verify log file contents after each operation
- Test with various username formats and special characters

### Property-Based Testing

Property-based tests will verify correctness properties hold across many inputs:

**PBT Library**: We'll use `hypothesis` for Python, which is the standard property-based testing library.

**Configuration**: Each property test will run a minimum of 100 iterations with randomly generated inputs.

**Test Properties**:

1. **Property 1 Test**: Generate random authentication events (different types, usernames, statuses) and verify each creates a log entry with correct fields
   - Generator: Random usernames, event types, success/failure status
   - Verification: Parse log file and verify entry exists with correct data

2. **Property 2 Test**: Generate random authentication events and immediately read the log file to verify entries are present
   - Generator: Random authentication events
   - Verification: Log entry is readable immediately after logging call

3. **Property 3 Test**: Generate random login/logout pairs with varying session durations and verify calculated duration matches expected
   - Generator: Random session durations (0 to 3600 seconds)
   - Verification: Logged duration ≈ actual duration (within ±2 seconds)

4. **Property 4 Test**: Generate random authentication events and verify all log entries can be parsed successfully
   - Generator: Random usernames (including special characters), event types
   - Verification: All log entries parse successfully and contain required fields

5. **Property 6 Test**: Simulate logging failures and verify authentication still succeeds
   - Generator: Random authentication attempts
   - Verification: Authentication succeeds even when logging fails

**Edge Cases Handled by Generators**:
- Usernames with special characters (pipes, newlines, unicode)
- Empty usernames
- Very long usernames
- Concurrent authentication events
- Missing session data

### Integration Testing

Integration tests will verify the logging system works with the actual Flask application:

1. **Test login flow**: Perform actual login through Flask test client and verify log entries
2. **Test TOTP flow**: Complete TOTP verification and verify log entries
3. **Test logout flow**: Perform logout and verify session duration is logged
4. **Test concurrent logins**: Simulate multiple concurrent logins and verify all are logged correctly

## Implementation Notes

1. **Log File Location**: The log file will be stored in `logs/auth_events.log` relative to the application root. The `logs` directory will be created if it doesn't exist.

2. **Log Rotation**: For production use, consider implementing log rotation using `RotatingFileHandler` to prevent the log file from growing indefinitely. This is not required for the initial implementation but should be considered for future enhancement.

3. **Thread Safety**: Python's logging module is thread-safe by default, so no additional locking is needed for concurrent requests.

4. **Performance**: File I/O is buffered by default, but we'll configure the logger to flush after each write to ensure immediate persistence (Property 2).

5. **Backwards Compatibility**: The logging system will work with both TOTP-enabled users and legacy users who don't use TOTP.

## Security Considerations

1. **Sensitive Data**: Log entries will NOT include passwords, TOTP codes, or other sensitive authentication data. Only usernames, timestamps, and event types are logged.
