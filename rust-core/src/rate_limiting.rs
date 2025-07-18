// Rate limiting implementation

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct RateLimitEntry {
    pub count: u32,
    pub window_start: Instant,
}

#[derive(Debug)]
pub struct RateLimiter {
    entries: Arc<Mutex<HashMap<String, RateLimitEntry>>>,
    max_requests: u32,
    window_duration: Duration,
}

impl RateLimiter {
    pub fn new(max_requests: u32, window_seconds: u64) -> Self {
        Self {
            entries: Arc::new(Mutex::new(HashMap::new())),
            max_requests,
            window_duration: Duration::from_secs(window_seconds),
        }
    }

    pub fn check_rate_limit(&self, client_id: &str) -> bool {
        let mut entries = self.entries.lock().unwrap();
        let now = Instant::now();

        // Clean up old entries
        entries.retain(|_, entry| now.duration_since(entry.window_start) < self.window_duration);

        // Check current client
        match entries.get_mut(client_id) {
            Some(entry) => {
                if now.duration_since(entry.window_start) >= self.window_duration {
                    // Reset window
                    entry.count = 1;
                    entry.window_start = now;
                    true
                } else if entry.count < self.max_requests {
                    // Within limits
                    entry.count += 1;
                    true
                } else {
                    // Rate limit exceeded
                    false
                }
            }
            None => {
                // New client
                entries.insert(
                    client_id.to_string(),
                    RateLimitEntry {
                        count: 1,
                        window_start: now,
                    },
                );
                true
            }
        }
    }

    pub fn get_remaining_requests(&self, client_id: &str) -> u32 {
        let entries = self.entries.lock().unwrap();
        match entries.get(client_id) {
            Some(entry) => {
                if Instant::now().duration_since(entry.window_start) >= self.window_duration {
                    self.max_requests
                } else {
                    self.max_requests.saturating_sub(entry.count)
                }
            }
            None => self.max_requests,
        }
    }

    pub fn get_reset_time(&self, client_id: &str) -> Option<Instant> {
        let entries = self.entries.lock().unwrap();
        entries
            .get(client_id)
            .map(|entry| entry.window_start + self.window_duration)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_rate_limiter_basic() {
        let limiter = RateLimiter::new(5, 60); // 5 requests per minute

        // Should allow first 5 requests
        for _ in 0..5 {
            assert!(limiter.check_rate_limit("client1"));
        }

        // Should block 6th request
        assert!(!limiter.check_rate_limit("client1"));
    }

    #[test]
    fn test_rate_limiter_different_clients() {
        let limiter = RateLimiter::new(2, 60);

        assert!(limiter.check_rate_limit("client1"));
        assert!(limiter.check_rate_limit("client2"));
        assert!(limiter.check_rate_limit("client1"));
        assert!(limiter.check_rate_limit("client2"));

        // Both clients should be at limit now
        assert!(!limiter.check_rate_limit("client1"));
        assert!(!limiter.check_rate_limit("client2"));
    }

    #[test]
    fn test_rate_limiter_window_reset() {
        let limiter = RateLimiter::new(2, 1); // 2 requests per second

        assert!(limiter.check_rate_limit("client1"));
        assert!(limiter.check_rate_limit("client1"));
        assert!(!limiter.check_rate_limit("client1"));

        // Wait for window to reset
        thread::sleep(Duration::from_secs(1));

        // Should allow requests again
        assert!(limiter.check_rate_limit("client1"));
    }

    #[test]
    fn test_remaining_requests() {
        let limiter = RateLimiter::new(5, 60);

        assert_eq!(limiter.get_remaining_requests("client1"), 5);

        limiter.check_rate_limit("client1");
        assert_eq!(limiter.get_remaining_requests("client1"), 4);

        limiter.check_rate_limit("client1");
        assert_eq!(limiter.get_remaining_requests("client1"), 3);
    }
}
