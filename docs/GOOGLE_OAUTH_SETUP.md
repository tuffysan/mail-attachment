# Google OAuth setup from the web interface

Mail Attachment Hub can store the Google OAuth application configuration in the
existing `system_metadata` table. No database migration is required.

The client secret is encrypted with `APP_SECRET_KEY`.

Open:

```text
Administration -> Google OAuth
```

or click **Anslut Gmail med Google**. If Google OAuth is not configured,
Mail Attachment Hub redirects automatically to the setup page.

## Wizard

1. Open Google Auth Platform directly from Mail Attachment Hub.
2. Enable Gmail API.
3. Create an OAuth client of type **Web application**.
4. Copy the exact callback URI displayed by Mail Attachment Hub into
   **Authorized redirect URIs**.
5. Paste Client ID and Client Secret into Mail Attachment Hub.
6. Click **Spara och anslut Google**.
7. The browser is redirected to Google.
8. After consent, the Gmail account is created automatically with the email
   address returned by Google.

## Important redirect URI requirement

Google web OAuth redirects normally require HTTPS and a hostname. Raw LAN IP
addresses such as `192.168.x.x` are not accepted. Localhost is exempt.

For an LXC installation, expose Mail Attachment Hub through an HTTPS hostname,
for example with a reverse proxy, and enter that hostname as **OAuth Base URL**:

```text
https://mail.example.com
```

The callback becomes:

```text
https://mail.example.com/api/v1/oauth/google/callback
```

## Stored metadata keys

```text
oauth.google.client_id
oauth.google.client_secret
oauth.google.public_base_url
```

The secret value is encrypted.
