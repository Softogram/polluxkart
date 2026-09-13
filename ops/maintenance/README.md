# Maintenance page for polluxkart.com

`index.html` in this folder is shown at polluxkart.com while the store is rebuilt.
It replaces the old app, which still loaded third-party Emergent scripts and could not reach its backend.

The page is one static file.
It has no JavaScript, no web fonts and no third-party requests, so there is nothing on it to break or leak.
It tells search engines not to index it (`noindex`), so the relaunch starts with a clean search listing.

## Why it shows business details

Razorpay reviews the website registered on a merchant account.
Indian e-commerce rules also expect seller contact details to be visible.
Showing the legal name, address, GSTIN and support contacts keeps both satisfied while the store is offline.

## Before you upload: fill in the placeholders

Replace every value in square brackets, such as `[SUPPORT EMAIL]`, with the real detail.
Then check that none are left:

```
grep -n '\[' ops/maintenance/index.html
```

That command should print nothing.

## How to upload

The old site is served by AWS CloudFront (a content delivery network that caches files close to visitors) from an S3 bucket (AWS file storage).
Find the bucket name in the CloudFront console, under the distribution for polluxkart.com, in the "Origins" tab.

1. Back up what is in the bucket today, in case you need it:
   ```
   aws s3 sync s3://<bucket-name> ./old-site-backup
   ```
2. Remove the old app files and upload the page:
   ```
   aws s3 rm s3://<bucket-name> --recursive
   aws s3 cp ops/maintenance/index.html s3://<bucket-name>/index.html --content-type "text/html; charset=utf-8" --cache-control "no-cache"
   ```
3. Make CloudFront serve the new file right away, instead of its cached copy:
   ```
   aws cloudfront create-invalidation --distribution-id <distribution-id> --paths "/*"
   ```
4. If the distribution sends missing pages to `index.html` (a common setting for single-page apps), every old URL now shows this page, which is what we want.

## How to check it worked

```
curl -s https://polluxkart.com | grep -c emergent
```

That should print `0`.
Open the site on a phone too, and confirm the contact details are correct.
