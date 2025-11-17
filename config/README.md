# Config Folder Overview

This directory stores configuration assets that the agent loads at runtime.

- `gmail_credentials.json`: OAuth client secret downloaded from Google Cloud.
- `gmail_token.json`: Access/refresh token generated after the first Gmail login flow. The file is created automatically; delete it to force a new authentication round.

Keep credentials out of version control and protect them with appropriate file permissions.
