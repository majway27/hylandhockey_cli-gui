# Rate Limiting Solution for Google API Integration

This document explains the rate limiting solution implemented to handle Google API 429 (Too Many Requests) errors gracefully during batch order processing.

## Overview

The rate limiting solution provides:

1. **Exponential Backoff Retry Logic** - Automatically retries failed API calls with increasing delays
2. **Configurable Rate Limiting** - User-adjustable settings for retry behavior and delays
3. **Graceful Error Handling** - Clear error messages and recovery options
4. **Batch Processing Protection** - Delays between batch operations to prevent overwhelming APIs

## Configuration

### Rate Limiting Settings

The rate limiting behavior can be configured in the `config.yaml` file under the `rate_limiting` section:

```yaml
rate_limiting:
  # Maximum number of retries for API calls
  max_retries: 3
  # Base delay in seconds before first retry
  base_delay: 1.0
  # Maximum delay in seconds (exponential backoff cap)
  max_delay: 60.0
  # Delay between batch operations in seconds
  batch_delay: 0.5
  # Delay between individual API calls in seconds
  api_call_delay: 0.1
  # Whether to use exponential backoff
  use_exponential_backoff: true
  # HTTP status codes to retry on
  retry_status_codes: [429, 500, 502, 503, 504]
```

### Configuration via GUI

You can also configure these settings through the GUI:

1. Navigate to **Configuration** → **Rate Limiting** tab
2. Adjust the settings as needed
3. Click **Save Configuration**

## How It Works

### Exponential Backoff Algorithm

When an API call fails with a retryable error (429, 500, 502, 503, 504):

1. **First retry**: Wait `base_delay` seconds
2. **Second retry**: Wait `base_delay * 2` seconds
3. **Third retry**: Wait `base_delay * 4` seconds
4. **Continue** until `max_delay` is reached

The actual delay includes random jitter (±10%) to prevent thundering herd problems.

### Rate Limiting Between Calls

- **API Call Delay**: Minimum time between individual API calls
- **Batch Delay**: Time to wait between batch operations
- **Automatic Throttling**: The system automatically respects these limits

### Error Handling

- **429 Errors**: Automatically retried with exponential backoff
- **Other Retryable Errors**: 500, 502, 503, 504 are also retried
- **Non-Retryable Errors**: Immediately fail without retry
- **Max Retries Exceeded**: Clear error message with recovery instructions

## Implementation Details

### Rate Limiting Module (`utils/rate_limiting.py`)

- `RateLimiter` class: Core rate limiting logic
- `rate_limited` decorator: Easy application to functions
- `batch_delay` decorator: Adds delays between batch operations
- `RateLimitExceededError`: Custom exception for rate limit failures

### Enhanced API Functions

The following functions now include rate limiting:

#### Google Sheets API
- `read_google_sheet_by_id_with_retry()`: Read sheet data with retry
- `update_cell_with_retry()`: Update cell with retry

#### Gmail API
- `create_gmail_draft_with_retry()`: Create draft with retry
- `send_gmail_with_retry()`: Send email with retry

### Batch Processing Integration

The batch orders view (`ui/views/batch_orders.py`) now:

- Catches `RateLimitExceededError` exceptions
- Provides clear user feedback about rate limiting
- Allows users to resume processing after rate limit recovery
- Logs rate limiting events for debugging

## Recommended Settings

### For Light Usage (1-10 orders per batch)
```yaml
rate_limiting:
  max_retries: 3
  base_delay: 1.0
  max_delay: 30.0
  batch_delay: 0.5
  api_call_delay: 0.1
  use_exponential_backoff: true
```

### For Heavy Usage (10+ orders per batch)
```yaml
rate_limiting:
  max_retries: 5
  base_delay: 2.0
  max_delay: 120.0
  batch_delay: 1.0
  api_call_delay: 0.2
  use_exponential_backoff: true
```

### For Development/Testing
```yaml
rate_limiting:
  max_retries: 2
  base_delay: 0.5
  max_delay: 10.0
  batch_delay: 0.1
  api_call_delay: 0.05
  use_exponential_backoff: false
```

## Troubleshooting

### Common Issues

1. **Still getting 429 errors**
   - Increase `api_call_delay` and `batch_delay`
   - Increase `max_retries`
   - Check if multiple instances are running

2. **Processing is too slow**
   - Decrease `api_call_delay` and `batch_delay`
   - Decrease `base_delay`
   - Consider reducing batch size

3. **Retries not working**
   - Check that `use_exponential_backoff` is enabled
   - Verify `retry_status_codes` includes 429
   - Check logs for specific error details

### Monitoring

Rate limiting events are logged with appropriate levels:

- **INFO**: Successful retries
- **WARNING**: Retry attempts with delays
- **ERROR**: Rate limit exceeded after all retries

### Google Cloud Console

You can monitor API usage in the Google Cloud Console:

1. Go to **APIs & Services** → **Dashboard**
2. Select **Google Sheets API** or **Gmail API**
3. View **Quotas** and **Usage** tabs
4. Monitor for rate limit violations

## Best Practices

1. **Start Conservative**: Begin with recommended settings and adjust based on usage
2. **Monitor Logs**: Watch for rate limiting warnings and adjust settings accordingly
3. **Batch Appropriately**: Don't process too many orders at once
4. **Respect Limits**: The system is designed to work within Google's quotas
5. **Test First**: Always test with small batches before large operations

## Future Enhancements

Potential improvements to consider:

1. **Dynamic Rate Limiting**: Adjust delays based on API response headers
2. **Quota Monitoring**: Track quota usage and warn before limits
3. **Circuit Breaker**: Temporarily disable operations during high error rates
4. **Distributed Rate Limiting**: Coordinate rate limits across multiple instances
5. **API-Specific Limits**: Different settings for different Google APIs 