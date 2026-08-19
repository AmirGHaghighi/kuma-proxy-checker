from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TesterConfig:
    test_url: str
    expected_status: int
    timeout_seconds: float
    retries: int
    retry_delay_seconds: float
