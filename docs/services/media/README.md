# media

Parent: [services/](../README.md) | Index: [docs/](../../README.md)

**Status: PLANNED, approved 2026-09-13. Built in slice S2.**

## Owns

Image uploads to S3, file checks, and image records with size and dimensions.
Schema: `media`.

## Promises

- Uploads go straight from the admin's browser to S3 through a presigned request (a short-lived upload permission) with a size limit and an allowed content type.
- After upload, a finalize step reads the file's first bytes to confirm it really is JPEG, PNG, WebP or AVIF. SVG is never accepted, because it can carry scripts.
- Stored keys are derived from the file's SHA-256 hash, so a file can never overwrite another and duplicates are stored once.
- Images are served only from the media domain through CloudFront, never from the API or the store's own address.
- Only admins can upload.

## Interface (planned)

`MediaApi`: create an upload permission; finalize an upload; get ready image records by ids (batch) with URLs, width and height.

## Endpoints (planned)

`POST /api/v1/admin/media/uploads`, `POST /api/v1/admin/media/uploads/{id}/finalize`.

## Events

Publishes `MediaFinalized` and `MediaRejected`.

## Refuses

- Files over the size limit, files whose bytes do not match an allowed image type, and SVG.
- Uploads from anyone who is not an admin.

## See also (do not follow recursively)

- [../../platform/security.md](../../platform/security.md) - why uploads are handled this way
