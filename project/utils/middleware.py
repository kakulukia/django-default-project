from django.utils.deprecation import MiddlewareMixin


class AccountFrameMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        match = request.resolver_match
        if match and match.func.__module__.startswith(("allauth.account.", "allauth.mfa.")):
            # The demo dialog may embed account pages, but only on the same origin.
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response
