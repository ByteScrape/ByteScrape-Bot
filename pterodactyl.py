import aiohttp
import asyncio
from utils.config import Config

config = Config()

class PterodactylAPI:
    def __init__(self, panel_url, api_key):
        """
        Initialize with the base URL of your Pterodactyl panel and an admin API key.
        :param panel_url: Base URL of your Pterodactyl panel (e.g., https://panel.example.com)
        :param api_key: Application (admin) API key from your Pterodactyl panel.
        """
        self.panel_url = panel_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def _get(self, endpoint, params=None):
        """
        Internal helper method to perform GET requests.
        :param endpoint: API endpoint starting with a slash (e.g., /api/application/users)
        :param params: Optional dictionary for query parameters.
        :return: Parsed JSON response.
        """
        url = f"{self.panel_url}{endpoint}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def _post(self, endpoint, payload=None):
        """
        Internal helper method to perform POST requests.
        :param endpoint: API endpoint starting with a slash.
        :param payload: Optional JSON payload.
        :return: Parsed JSON response.
        """
        url = f"{self.panel_url}{endpoint}"
        async with self.session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()

    async def get_user_by_email(self, email):
        """
        Retrieve the first user matching the provided email.
        :param email: User's email address.
        :return: User object (dictionary) if found.
        :raises Exception: If no user is found.
        """
        endpoint = "/api/application/users"
        params = {"filter[email]": email}
        data = await self._get(endpoint, params)
        if data.get('meta', {}).get('pagination', {}).get('total', 0) == 0:
            raise Exception(f"User with email {email} not found")
        return data["data"][0]

    async def get_servers_by_user_id(self, user_id):
        """
        Retrieve a list of servers associated with the specified user ID.
        :param user_id: The unique identifier of the user.
        :return: List of servers.
        """
        endpoint = f"/api/application/users/{user_id}?include=servers"
        data = await self._get(endpoint)

        server = []

        for x in data["attributes"]["relationships"]["servers"]["data"]:
            server_id = x["attributes"]["id"]
            server.append(server_id)
        return server

    async def get_servers_by_email(self, email):
        """
        Retrieve all servers for a user identified by their email.
        :param email: Email address associated with the Pterodactyl user.
        :return: List of servers.
        """
        user = await self.get_user_by_email(email)
        user_id = user["attributes"].get("id")
        if not user_id:
            raise Exception("User record does not contain an ID attribute")
        return await self.get_servers_by_user_id(user_id)

    async def suspend_server(self, server_identifier):
        """
        Suspend a single server using its identifier.
        :param server_identifier: Unique identifier for the server (often a UUID).
        :return: Result of the suspend operation.
        """
        # The suspend endpoint for a server. The API may not require any payload.
        endpoint = f"/api/application/servers/{server_identifier}/suspend"
        return await self._post(endpoint, payload={})

    async def suspend_servers_by_email(self, email):
        """
        Suspend all servers associated with the provided user email.
        :param email: The user's email.
        :return: List of results for the suspend operations.
        """
        servers = await self.get_servers_by_email(email)
        tasks = []
        for server in servers:
            # It is common for server objects to store the unique server identifier under "identifier".
            server_identifier = server["attributes"].get("identifier")
            if server_identifier:
                tasks.append(self.suspend_server(server_identifier))
        if not tasks:
            raise Exception("No servers found with a valid identifier to suspend")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


# Example usage
async def main():
    PANEL_URL = config.pterodactyl_url  # Your Pterodactyl panel URL
    API_KEY = config.pterodactyl_token
    email = "spam.yuuto@gmail.com"  # Update with the target user's email

    async with PterodactylAPI(PANEL_URL, API_KEY) as api:
        try:
            x = await api.get_servers_by_email(email)
            print(x)
            for y in x:
                await api.suspend_server(y)
            """print("Suspend results:")
            for res in results:
                print(res)"""
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    asyncio.run(main())
