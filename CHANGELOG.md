# CHANGELOG

## [0.3.0] - 2025-08-09

### Changed
- Replaced `enable()` / `disable()` methods with environment variable `SCOPE_TIMER_ENABLE`
- Split `profile()` into `profile_block()` (context manager) and `profile_func()` (decorator)

### Removed
- Deprecated `enable()` / `disable()` methods
- Made `begin()` / `end()` private (not part of public API)

### Performance
- Greatly reduced overhead when profiling is disabled (`SCOPE_TIMER_ENABLE=0`)

---

## [0.2.0] - 2025-08-06

### Added
- `enable()` and `disable()` methods to toggle profiling at runtime

