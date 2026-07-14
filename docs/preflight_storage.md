# Preflight file storage

## Development

With `COAPPRAISER_STORAGE_BACKEND=local` (the default when no R2 bucket is configured), Django stores uploads under the local `media/` directory. This is suitable for local testing only.

## Production

Use Cloudflare R2 through its S3-compatible API. Set:

```text
COAPPRAISER_STORAGE_BACKEND=r2
R2_ACCOUNT_ID=...
R2_BUCKET_NAME=coappraiser-private
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
```

`R2_ENDPOINT_URL` is optional and defaults to `https://<account-id>.r2.cloudflarestorage.com`.

The Django storage backend uses private objects, signed querystring URLs, no public ACL, overwrite protection, and private cache headers. The application does not publish `/media/` and the Preflight download route checks review ownership before streaming a file.

Deleting a Preflight review deletes each local or R2 object before deleting the review records. Configure R2 lifecycle rules separately if the product later adds automatic retention expiration.

Do not put R2 credentials in Git, committed `.env` files, browser code, or model prompts. Store them as Railway environment variables.
