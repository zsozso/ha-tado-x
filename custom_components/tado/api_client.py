"""Preserve Home Assistant's HTTP identification and quota tracking with PyTado X."""

from typing import Any

from PyTado.interface import Tado as BaseTado
from requests import Response, Session

from homeassistant.const import APPLICATION_NAME, __version__


class Tado(BaseTado):
    """Adapt the X-capable client to the HTTP features used by Home Assistant."""

    def __init__(self, user_agent: str | None = None, **kwargs: Any) -> None:
        """Create a client with a quota-aware HTTP session."""
        self._rate_limit: dict[str, str] = {}
        session = Session()
        session.headers['User-Agent'] = user_agent or f'{APPLICATION_NAME}/{__version__}'
        session.hooks['response'].append(self._track_quota)
        super().__init__(http_session=session, **kwargs)

    def _track_quota(self, response: Response, **kwargs: Any) -> Response:
        """Read daily quota headers without retaining response content or secrets."""
        policy = response.headers.get('RateLimit-Policy')
        limit = response.headers.get('RateLimit')
        if policy and limit:
            policy_parts = dict(part.split('=', 1) for part in policy.split(';')[1:] if '=' in part)
            limit_parts = dict(part.split('=', 1) for part in limit.split(';')[1:] if '=' in part)
            self._rate_limit = {
                'total': policy_parts.get('q', '0'),
                'remaining': limit_parts.get('r', '0'),
                'reset': policy_parts.get('w', '0'),
            }
        return response

    def rate_limit_info(self) -> dict[str, str]:
        """Return the quota information from the last applicable response."""
        return dict(self._rate_limit)
