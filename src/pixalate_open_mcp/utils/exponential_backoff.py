import secrets
import time


def exponential_backoff(initial_delay=1, max_retries=10, max_delay=60, jitter=True):
    """
    A decorator to implement exponential backoff with optional jitter.

    Args:
        initial_delay (int): The initial delay in seconds.
        max_retries (int): The maximum number of retry attempts.
        max_delay (int): The maximum delay allowed between retries.
        jitter (bool): Whether to add random jitter to the delay.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_attempt = 0
            current_delay = initial_delay

            while current_attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    current_attempt += 1
                    if current_attempt >= max_retries:
                        raise

                    # Calculate delay with exponential backoff
                    calculated_delay = min(current_delay * (2 ** (current_attempt - 1)), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        jitter_amount = calculated_delay * secrets.SystemRandom().uniform(0, 0.5)  # Up to 50% of delay
                        calculated_delay += jitter_amount

                    print(
                        f"Operation failed. Retrying in {calculated_delay:.2f} seconds (Attempt {current_attempt}/{max_retries})..."
                    )
                    time.sleep(calculated_delay)
                    current_delay = calculated_delay  # Update current_delay for next iteration
            return None  # Should not be reached if exception is always re-raised

        return wrapper

    return decorator
