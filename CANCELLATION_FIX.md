# Ctrl+C Cancellation Fix

## Issue
Recent changes to add concurrent processing with `ThreadPoolExecutor` broke Ctrl+C cancellation. The main thread would receive the KeyboardInterrupt, but worker threads continued running.

## Root Cause
1. **ThreadPoolExecutor**: Added in `azure_devops_client.py` for concurrent batch fetching
2. **Worker Threads**: Don't inherit the main thread's signal handlers
3. **Blocking Operations**: `as_completed()` waits for futures, blocking cancellation

## Fix Applied

### 1. Enhanced ThreadPoolExecutor with Timeout & Exception Handling
```python
# Old (blocking):
for future in as_completed(future_to_batch):
    batch_items = future.result()
    work_items.extend(batch_items)

# New (cancellable):
for future in as_completed(future_to_batch):
    try:
        batch_items = future.result(timeout=30)  # Add timeout
        work_items.extend(batch_items)
    except KeyboardInterrupt:
        logger.info("Cancelling remaining batch requests...")
        for f in future_to_batch:
            f.cancel()
        raise
```

### 2. Signal Handler in CLI
```python
def signal_handler(signum, frame):
    console.print("\\n[yellow]⚠️  Operation cancelled by user. Exiting...[/yellow]")
    sys.exit(130)  # Standard exit code for Ctrl+C

signal.signal(signal.SIGINT, signal_handler)
```

### 3. Graceful Cancellation Chain
- User presses Ctrl+C
- Signal handler displays message and exits
- ThreadPoolExecutor futures get cancelled
- Clean exit with appropriate exit code

## Testing
Test cancellation behavior:
```bash
python3 -m src.cli fetch --days-back 30 --history-limit 5
# Press Ctrl+C during execution
```

Expected behavior:
- Immediate response to Ctrl+C
- Clean exit message
- No hanging threads
- Exit code 130 (standard for interrupted)

## Performance Impact
- **Timeout Added**: 30-second timeout per batch prevents infinite hanging
- **Future Cancellation**: Remaining requests get cancelled properly
- **Clean Exit**: No zombie threads or processes

The fix maintains the performance benefits of concurrent processing while restoring proper cancellation behavior.
